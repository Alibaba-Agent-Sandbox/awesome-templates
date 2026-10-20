#!/usr/bin/env python3
"""Deploy one template to Alibaba Cloud Express and run its smoke commands.

The harness reads ``generation``, ``start_cmd``, ``ready_cmd``, and ``smoke``
from ``template.yaml``. It deploys with ``abx template deploy`` (generation 2),
creates one sandbox, calls each smoke command through ``abx run`` and through
``await Sandbox.connect`` / ``await sb.run``, and always deletes that sandbox and that
template in a ``finally`` block.

A passing run writes ``<template>/evidence/express-<YYYY-MM-DD>.json`` only after
owned sandbox/template cleanup succeeds. Failed or ambiguous attempts retain a
private owned intent; ``--recover-intent PATH`` retries exact owned recovery.
A failed or blocked run does not write evidence and does not list the provider
as verified. Known CLI/SDK failures (an older ``abx`` or SDK) exit 2 with the
issue URL. Other failures exit 1.

``abx template deploy`` still does the build and the ACR push. This harness
does not push by itself. Concurrent harnesses take an exclusive flock on
``/tmp/abx-acr-push.lock`` (override with ``ABX_ACR_PUSH_LOCK``) for the whole
deploy, because the CLI has no separate push step and no push lock of its own.
The deploy is killed when CLI output stops for ``--idle-timeout`` seconds, not
when a fixed wall clock elapses. ``--timeout`` is forwarded to ``abx`` as the
READY poll budget. A safety ``--wall-timeout`` (default max(21600, ``--timeout``))
still bounds a deploy that keeps printing. A stalled push is retried
``--push-retries`` times (default 2). The child environment drops ``CI`` and
the other variables ``abx`` treats as CI, because that mode hides push lines
and the idle timer would then see a healthy upload as idle. ``finally`` kills
the deploy process group and any ``docker push`` whose command line contains
this run's alias.

Environment (never commit the values):

- ``ABX``: command that runs the CLI, for example
  ``node /path/to/agent-sandbox/dist/bin/abx.js``. ``abx`` on ``PATH`` is the fallback.
- ``ACR_NAMESPACE``: registry namespace for the image push.
- ``ALICLOUD_ACCESS_KEY_ID`` and ``ALICLOUD_ACCESS_KEY_SECRET``: image push and
  template registration. ``abx`` also reads them from the current ``.env``.
- ``ABX_SANDBOX_API_KEY``, ``ABX_SANDBOX_BASE_URL``, ``ABX_SANDBOX_DOMAIN``:
  create and command calls.
- ``ALIBABA_CLOUD_REGION_ID``: region (default in the CLI is ``cn-hangzhou``).
- ``ABX_BASE_IMAGE_TAG``: optional pin, CLI default ``v0.0.49``.
- ``ABX_SERVER_SDK_SOURCE``: optional path to a ``server-sdk`` tree. ``abx``
  injects that wheel into the image build.

Unset ``ABX_PROVIDER`` before running. Keep ``HOME`` as the operator home so
``abx`` can read ``~/.abx``. This script drops ``ABX_PROVIDER`` from the child
environment and does not print secret values.

Exit status: 0 passed, 2 blocked on a known CLI/SDK bug, 1 any other failure.
"""
from __future__ import annotations

import argparse
import ast
import fcntl
import hashlib
import json
import os
import re
import shlex
import signal
import subprocess
import sys
import threading
import tempfile
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator

try:
    import yaml
except ImportError:  # pragma: no cover
    print("express_e2e.py needs PyYAML (pip install pyyaml)", file=sys.stderr)
    raise SystemExit(1)

DEFAULT_START = "agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py"
DEFAULT_READY = "agent-sandbox-server healthcheck --port 9000"
DEFAULT_PUSH_LOCK = Path("/tmp/abx-acr-push.lock")
DEFAULT_IDLE_TIMEOUT = 180
DEFAULT_PUSH_RETRIES = 2
OWNED_ACR_TAG = "review"

# Older binaries. Current main accepts a string base, reads start/ready from
# template.yaml, envelopes gen2 envd streams, and does not treat the Express
# gateway token as a server login. The strings stay so an older binary still
# exits 2 with a pointer instead of a traceback.
BLOCKERS = (
    (
        "base must be a mapping",
        "agent-sandbox#12",
        "https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues/12",
    ),
    (
        "startCommand is only supported when updating a generation 2",
        "agent-sandbox#13",
        "https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues/13",
    ),
    (
        "AuthError",
        "agent-sandbox#14 / python-sdk#17",
        "https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues/14",
    ),
    (
        "promised",
        "python-sdk#15",
        "https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues/15",
    ),
    (
        "protocol error",
        "python-sdk#15",
        "https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues/15",
    ),
)


@dataclass
class Smoke:
    command: str
    args: dict[str, Any]
    expect: Any


@dataclass
class Options:
    template_dir: Path
    smoke: list[Smoke]
    start_cmd: str
    ready_cmd: str
    generation: int
    deploy_timeout: int
    idle_timeout: int
    wall_timeout: int
    push_retries: int
    alias: str
    plan: bool = False
    template_name: str = ""
    template_version: str = ""
    build_mode: str = "dockerfile"
    image_ref: str = ""
    image_provenance: dict | None = None
    sandbox_timeout: int = 300
    sandbox_create: str = "cli"


@dataclass
class Proc:
    returncode: int
    stdout: str
    stderr: str


Runner = Callable[[list[str], float], Proc]
Sdk = Callable[[str, str, dict[str, Any]], Any]
HARNESS_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

# (pgid, alias) for deploys this process started and has not reaped yet.
_ACTIVE_DEPLOYS: list[tuple[int, str]] = []


def acr_lock_path() -> Path:
    raw = os.environ.get("ABX_ACR_PUSH_LOCK")
    return Path(raw) if raw else DEFAULT_PUSH_LOCK


@contextmanager
def acr_push_lock(path: Path | None = None) -> Iterator[None]:
    """Exclusive cross-process lock around one ``abx template deploy``.

    The CLI push sits inside that command. Holding the lock for the whole
    deploy serializes uploads from concurrent harnesses. The lock is released
    when this process exits even if it does not unlock.
    """
    lock_path = path or acr_lock_path()
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o644)
    announced = False
    waited = 0
    try:
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if not announced or waited % 15 == 0:
                    holder = ""
                    try:
                        holder = os.pread(fd, 64, 0).decode("utf-8", "replace").strip()
                    except OSError:
                        holder = ""
                    who = f" held by pid {holder}" if holder.isdigit() else ""
                    print(
                        f"waiting for ACR push lock {lock_path}{who}; another deploy is pushing",
                        flush=True,
                    )
                    announced = True
                time.sleep(1)
                waited += 1
        os.ftruncate(fd, 0)
        os.lseek(fd, 0, os.SEEK_SET)
        os.write(fd, f"{os.getpid()}\n".encode())
        print(f"acquired ACR push lock {lock_path}", flush=True)
        yield
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)
        print(f"released ACR push lock {lock_path}", flush=True)


def _kill_process_group(pid: int) -> None:
    try:
        os.killpg(pid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError, OSError):
        return
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.05)
    try:
        os.killpg(pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError, OSError):
        pass


def kill_docker_pushes(marker: str) -> list[int]:
    """SIGKILL ``docker push`` processes whose command line contains ``marker``.

    A harness timeout used to kill only ``abx``. The push is a grandchild and
    kept the registry socket. ``marker`` is the deploy alias (long enough that
    a short string cannot match an unrelated push).
    """
    if len(marker) < 8:
        return []
    killed: list[int] = []
    proc_root = Path("/proc")
    try:
        entries = list(proc_root.iterdir())
    except OSError:
        return killed
    for entry in entries:
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        try:
            raw = (entry / "cmdline").read_bytes()
        except OSError:
            continue
        command = raw.replace(b"\0", b" ").decode("utf-8", "replace")
        if "docker" not in command or " push " not in f" {command} ":
            continue
        if marker not in command:
            continue
        try:
            os.kill(pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            continue
        killed.append(pid)
    if killed:
        print(f"stopped docker push for {marker}: pids {killed}", flush=True)
    return killed


def stop_deploy_processes(alias: str) -> None:
    """Kill deploy process groups this process still tracks, then matching pushes."""
    leftover = [item for item in _ACTIVE_DEPLOYS if item[1] == alias]
    for pgid, _marker in leftover:
        _kill_process_group(pgid)
    _ACTIVE_DEPLOYS[:] = [item for item in _ACTIVE_DEPLOYS if item[1] != alias]
    kill_docker_pushes(alias)


def _pump(pipe: Any, chunks: list[str], progress: dict[str, float]) -> None:
    try:
        while True:
            data = pipe.read(4096)
            if not data:
                break
            chunks.append(data)
            progress["at"] = time.monotonic()
    finally:
        try:
            pipe.close()
        except OSError:
            pass


def run_monitored(
    argv: list[str],
    *,
    idle_timeout: float,
    wall_timeout: float,
    marker: str = "",
    env: dict[str, str] | None = None,
) -> Proc:
    """Run ``argv`` in its own session. Kill the group when output goes idle.

    ``idle_timeout`` is a no-progress limit: any new stdout or stderr byte
    resets it. ``wall_timeout`` is the hard cap, including a deploy that is
    still printing. ``marker`` is recorded so ``finally`` can stop a ``docker
    push`` that outlives the CLI.
    """
    child_env = os.environ.copy() if env is None else dict(env)
    child_env.pop("ABX_PROVIDER", None)
    # abx treats these as CI and then suppresses per-line logs, including
    # `docker push` status under --json --verbose. The idle timer watches those lines.
    for key in (
        "CI",
        "GITHUB_ACTIONS",
        "GITLAB_CI",
        "JENKINS_URL",
        "TRAVIS",
        "CIRCLECI",
        "BITBUCKET_PIPELINES",
        "TF_BUILD",
        "CODEBUILD_BUILD_ID",
    ):
        child_env.pop(key, None)
    try:
        proc = subprocess.Popen(
            argv,
            env=child_env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
    except OSError as exc:
        return Proc(127, "", f"failed to start {argv[0]}: {exc}")

    pgid = proc.pid
    if marker:
        _ACTIVE_DEPLOYS.append((pgid, marker))
    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []
    progress = {"at": time.monotonic()}
    started = progress["at"]
    threads = [
        threading.Thread(target=_pump, args=(proc.stdout, stdout_chunks, progress), daemon=True),
        threading.Thread(target=_pump, args=(proc.stderr, stderr_chunks, progress), daemon=True),
    ]
    for thread in threads:
        thread.start()
    reason = ""
    try:
        while True:
            # Keep the original leader unreaped until its process group is
            # stopped; poll()/wait() here would release the PID/PGID identity.
            exited = os.waitid(os.P_PID, proc.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
            now = time.monotonic()
            if exited is not None:
                break
            if now - progress["at"] >= idle_timeout:
                reason = "idle"
                print(
                    f"no CLI output for {idle_timeout:.0f}s; stopping process group {pgid}"
                    + (f" and docker push {marker}" if marker else ""),
                    flush=True,
                )
                _kill_process_group(pgid)
                if marker:
                    kill_docker_pushes(marker)
                break
            if now - started >= wall_timeout:
                reason = "wall"
                print(
                    f"deploy wall clock {wall_timeout:.0f}s exceeded; stopping process group {pgid}",
                    flush=True,
                )
                _kill_process_group(pgid)
                if marker:
                    kill_docker_pushes(marker)
                break
            time.sleep(0.1)
    finally:
        try:
            os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.wait(timeout=5)
        for thread in threads:
            thread.join(timeout=2)
        if marker:
            _ACTIVE_DEPLOYS[:] = [item for item in _ACTIVE_DEPLOYS if item[0] != pgid]
            # A push reparented during the kill still matches the alias.
            kill_docker_pushes(marker)

    stdout = "".join(stdout_chunks)
    stderr = "".join(stderr_chunks)
    if reason == "idle":
        stderr += (
            f"\nno ACR push progress for {idle_timeout:.0f}s "
            f"(no new CLI output). Stopped process group {pgid}.\n"
        )
        return Proc(124, stdout, stderr)
    if reason == "wall":
        stderr += (
            f"\ndeploy wall clock {wall_timeout:.0f}s exceeded while the CLI was still running. "
            f"Stopped process group {pgid}.\n"
        )
        return Proc(124, stdout, stderr)
    return Proc(proc.returncode or 0, stdout, stderr)


def scrub(text: str) -> str:
    redacted = text
    for key, value in os.environ.items():
        if not value or len(value) < 8:
            continue
        if re.search(r"(KEY|SECRET|TOKEN|PASSWORD)", key, re.IGNORECASE):
            redacted = redacted.replace(value, "***")
    return redacted


def classify_blocker(text: str) -> tuple[str, str] | None:
    for needle, label, url in BLOCKERS:
        if needle in text:
            return label, url
    if re.search(r'"code"\s*:\s*"unauthorized"', text) or "unauthorized" in text and "401" in text:
        return (
            "agent-sandbox#14 / python-sdk#17",
            "https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues/17",
        )
    return None


def _load_yaml(template_dir: Path) -> dict[str, Any]:
    path = template_dir / "template.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"{path} is not a mapping")
    return data


def smoke_from_yaml(data: dict[str, Any]) -> list[Smoke]:
    raw = data.get("smoke") or []
    if not isinstance(raw, list):
        raise SystemExit("template.yaml smoke must be a list")
    found: list[Smoke] = []
    for item in raw:
        if not isinstance(item, dict) or not item.get("command"):
            raise SystemExit(f"bad smoke item: {item!r}")
        args = item.get("args") or {}
        if not isinstance(args, dict):
            raise SystemExit("smoke.args must be a mapping")
        found.append(Smoke(str(item["command"]), dict(args), item.get("expect")))
    return found


def parse_smoke_json(text: str) -> list[Smoke]:
    payload = json.loads(text)
    if not isinstance(payload, list):
        raise SystemExit("--smoke-json must be a list")
    return smoke_from_yaml({"smoke": payload})


def build_options(argv: list[str] | None = None) -> Options:
    parser = argparse.ArgumentParser(description="Express L2 harness for one template.")
    parser.add_argument("template", type=Path)
    parser.add_argument("--build", choices=("dockerfile", "steps", "image"), default="dockerfile",
                        help="Explicit image deployment path. Steps needs a materialized manifest.")
    parser.add_argument("--image-ref", default="", help="Nonce-owned ACR review tag bound to checked digest for --build image")
    parser.add_argument("--image-proof", type=Path, help="Verified public CI archive/source/registry proof")
    parser.add_argument("--sandbox-timeout", type=int, default=300, help="Owned sandbox lifetime, separate from build readiness")
    parser.add_argument("--sandbox-create", choices=("cli", "sdk"), default="cli",
                        help="Select actual CLI or Python SDK sandbox creation; both keep CLI/SDK smoke and owned cleanup")
    parser.add_argument("--start-cmd", default=None)
    parser.add_argument("--ready-cmd", default=None)
    parser.add_argument("--generation", type=int, default=None)
    parser.add_argument(
        "--timeout",
        type=int,
        default=900,
        help="Seconds forwarded to abx template deploy --timeout (READY poll). Not a push wall clock.",
    )
    parser.add_argument(
        "--idle-timeout",
        type=int,
        default=DEFAULT_IDLE_TIMEOUT,
        help="Kill the deploy when CLI output is idle this many seconds (default 180).",
    )
    parser.add_argument(
        "--wall-timeout",
        type=int,
        default=0,
        help="Safety cap for one deploy attempt. 0 means max(21600, --timeout).",
    )
    parser.add_argument(
        "--push-retries",
        type=int,
        default=DEFAULT_PUSH_RETRIES,
        help="Extra attempts after a stalled or failed ACR push (default 2).",
    )
    parser.add_argument("--alias", default=None, help="Remote template name. Default is a unique e2e- name.")
    parser.add_argument("--smoke-json", default=None, help="JSON list overriding template.yaml smoke.")
    parser.add_argument("--command", default=None, help="Single smoke command when the template has no smoke list.")
    parser.add_argument("--arg", action="append", default=[], help="KEY=VALUE for --command. Repeatable.")
    parser.add_argument("--expect", default=None, help="Exact result expected from --command.")
    parser.add_argument("--plan", action="store_true", help="Print the deploy plan and exit.")
    args = parser.parse_args(argv)

    template_dir = args.template.resolve()
    if not (template_dir / "template.yaml").is_file():
        raise SystemExit(f"no template.yaml in {template_dir}")
    data = _load_yaml(template_dir)
    image_provenance = None
    if args.sandbox_timeout < 1:
        raise SystemExit("--sandbox-timeout must be positive")
    if args.build == "image":
        if not args.image_ref or not args.image_proof:
            raise SystemExit("--build image requires --image-ref and --image-proof")
        try:
            try:
                from .ci_image import validate_proof
            except ImportError:
                from ci_image import validate_proof
            image_provenance = validate_proof(template_dir, json.loads(args.image_proof.read_text()), args.image_ref)
        except (ValueError, OSError) as exc:
            raise SystemExit("invalid image proof: " + str(exc)) from None
    elif args.image_ref or args.image_proof:
        raise SystemExit("image options require --build image")
    if args.smoke_json:
        smoke = parse_smoke_json(args.smoke_json)
    elif args.command:
        arg_map: dict[str, Any] = {}
        for pair in args.arg:
            if "=" not in pair:
                raise SystemExit(f"--arg must be KEY=VALUE, got {pair!r}")
            key, value = pair.split("=", 1)
            arg_map[key] = value
        smoke = [Smoke(args.command, arg_map, args.expect)]
    else:
        smoke = smoke_from_yaml(data)
    if not smoke:
        raise SystemExit("no smoke commands: add template.yaml smoke, --smoke-json, or --command")

    start = args.start_cmd or data.get("start_cmd") or DEFAULT_START
    ready = args.ready_cmd or data.get("ready_cmd") or DEFAULT_READY
    generation = args.generation if args.generation is not None else int(data.get("generation") or 2)
    if args.idle_timeout < 1:
        raise SystemExit("--idle-timeout must be >= 1")
    if args.push_retries < 0:
        raise SystemExit("--push-retries must be >= 0")
    # 21600s is a safety cap, not the progress limit. A 1GB image at the
    # ~35KB/s seen on a contended ACR link needs several hours if it keeps moving.
    wall = args.wall_timeout if args.wall_timeout > 0 else max(21600, args.timeout)
    raw_alias = args.alias or f"e2e-{template_dir.name}-{uuid.uuid4().hex[:8]}"
    alias = re.sub(r"[^a-z0-9-]+", "-", raw_alias.lower())
    alias = re.sub(r"-+", "-", alias).strip("-")[:63].strip("-")
    return Options(
        template_dir=template_dir,
        smoke=smoke,
        start_cmd=str(start),
        ready_cmd=str(ready),
        generation=generation,
        deploy_timeout=args.timeout,
        idle_timeout=args.idle_timeout,
        wall_timeout=wall,
        push_retries=args.push_retries,
        alias=alias,
        plan=args.plan,
        template_name=str(data.get("name") or template_dir.name),
        template_version=str(data.get("version") or ""),
        build_mode=args.build,
        image_ref=args.image_ref,
        image_provenance=image_provenance,
        sandbox_timeout=args.sandbox_timeout,
        sandbox_create=args.sandbox_create,
    )


def plan_document(options: Options) -> dict[str, Any]:
    return {
        "template": str(options.template_dir),
        "name": options.template_name,
        "version": options.template_version,
        "alias": options.alias,
        "build_mode": options.build_mode,
        "registration_operation": "abx template create" if options.build_mode == "image" else "abx template deploy",
        "sandbox_timeout": options.sandbox_timeout,
        "sandbox_create": "python-sdk-Sandbox.create" if options.sandbox_create == "sdk" else "abx create",
        "harness_sha256": HARNESS_SHA256,
        "acr_repo": options.alias if options.build_mode == "dockerfile" else None,
        "acr_tag": OWNED_ACR_TAG if options.build_mode == "dockerfile" else None,
        "generation": options.generation,
        "start_cmd": options.start_cmd,
        "ready_cmd": options.ready_cmd,
        "deploy_timeout": options.deploy_timeout,
        "idle_timeout": options.idle_timeout,
        "wall_timeout": options.wall_timeout,
        "push_retries": options.push_retries,
        "acr_push_lock": str(acr_lock_path()) if options.build_mode == "dockerfile" else None,
        "smoke": [
            {"command": item.command, "args": item.args, "expect": item.expect} for item in options.smoke
        ],
    }


def _abx_argv(args: list[str]) -> list[str]:
    spec = os.environ.get("ABX") or "abx"
    return shlex.split(spec) + args


def default_runner(args: list[str], timeout: float) -> Proc:
    """Run one abx command. Silence for ``timeout`` seconds kills the process group."""
    return run_monitored(_abx_argv(args), idle_timeout=timeout, wall_timeout=timeout)


def _retryable_deploy(proc: Proc) -> bool:
    if proc.returncode == 0:
        return False
    text = proc.stdout + "\n" + proc.stderr
    if classify_blocker(text):
        return False
    if "Docker build failed" in text or "dockerfile parse" in text.lower():
        return False
    if proc.returncode == 124:
        return True
    needles = (
        "no ACR push progress",
        "deploy wall clock",
        "Pushing to ACR",
        "Docker push failed",
        "ACRPushError",
        "connection reset by peer",
        "i/o timeout",
    )
    return any(needle in text for needle in needles)


def _deploy_with_retries(options: Options, deploy_args: list[str], runner: Runner | None) -> Proc:
    attempts = 1 if options.build_mode == "image" else options.push_retries + 1
    last = Proc(1, "", "deploy was not attempted")
    for attempt in range(1, attempts + 1):
        print(
            f"deploy attempt {attempt}/{attempts} alias={options.alias} "
            f"idle_timeout={options.idle_timeout}s wall_timeout={options.wall_timeout}s "
            f"abx --timeout {options.deploy_timeout}",
            flush=True,
        )
        if runner is None:
            last = run_monitored(
                _abx_argv(deploy_args),
                idle_timeout=float(options.idle_timeout),
                wall_timeout=float(options.wall_timeout),
                marker=options.alias,
            )
        else:
            last = runner(deploy_args, float(options.wall_timeout))
        if last.returncode == 0:
            return last
        text = last.stdout + "\n" + last.stderr
        if classify_blocker(text):
            print(f"deploy attempt {attempt} matched a known blocker; not retrying", flush=True)
            return last
        if attempt >= attempts or not _retryable_deploy(last):
            if attempt < attempts:
                print(f"deploy attempt {attempt} failed and will not be retried", flush=True)
            else:
                print(f"deploy failed after {attempts} attempt(s)", flush=True)
            return last
        print(
            f"deploy attempt {attempt} stalled or the ACR push failed; "
            f"stopping leftover docker push processes for {options.alias} and retrying",
            flush=True,
        )
        stop_deploy_processes(options.alias)
    return last


def _json_objects(text: str) -> list[Any]:
    found: list[Any] = []
    decoder = json.JSONDecoder()
    index = 0
    while index < len(text):
        start = text.find("{", index)
        if start < 0:
            break
        try:
            payload, end = decoder.raw_decode(text, start)
        except json.JSONDecodeError:
            index = start + 1
            continue
        if isinstance(payload, dict):
            found.append(payload)
        index = end
    return found


def _last_json(proc: Proc) -> dict[str, Any] | None:
    stdout_objs = [item for item in _json_objects(proc.stdout) if isinstance(item, dict)]
    stderr_objs = [item for item in _json_objects(proc.stderr) if isinstance(item, dict)]
    id_keys = ("TemplateID", "templateID", "ID", "id", "result")
    for payload in reversed(stdout_objs + stderr_objs):
        if any(key in payload for key in id_keys):
            return payload
    if stdout_objs:
        return stdout_objs[-1]
    if stderr_objs:
        return stderr_objs[-1]
    return None


def _matches(actual: Any, expect: Any) -> bool:
    if expect is None:
        return True
    if isinstance(actual, str) and isinstance(expect, str):
        return actual.strip() == expect.strip()
    return actual == expect


def _cli_args(item: Smoke) -> list[str]:
    typed = any(not isinstance(value, str) for value in item.args.values())
    if typed:
        return ["--json-args", json.dumps(item.args)]
    return [flag for key, value in item.args.items() for flag in ("--arg", f"{key}={value}")]


def _sdk_version() -> str:
    try:
        import agent_sandbox

        return str(getattr(agent_sandbox, "__version__", "unknown"))
    except Exception:
        return "unknown"


def image_digest(image_ref: str) -> str:
    """Read the actual owned registry tag through verified crane and RAM auth."""
    try:
        from .ci_image_archive import crane_call
    except ImportError:
        from ci_image_archive import crane_call
    binary=os.environ.get("ABX_IMAGE_CRANE", "")
    if not binary:
        raise RuntimeError("verified crane path is required for live image digest readback")
    return crane_call(binary,["digest",image_ref],os.environ["ABX_IMAGE_REGISTRY_USERNAME"],
                      os.environ["ABX_IMAGE_REGISTRY_PASSWORD"],90)


def default_sdk_create(template_id: str, timeout: int) -> str:
    """Create through the native Python API, returning the known ID for journaling."""
    import asyncio
    from agent_sandbox.api.sandbox import Sandbox

    async def create() -> str:
        sandbox = await Sandbox.create(template=template_id, timeout=timeout)
        sandbox_id = sandbox.id
        try:
            await sandbox.close()
        except Exception:
            # Local client shutdown must not hide an already-created owned ID.
            pass
        return sandbox_id

    return asyncio.run(create())


def default_sdk(sandbox_id: str, command: str, args: dict[str, Any]) -> Any:
    """Call a native named command, then close the borrowed local client.

    The root standard Sandbox is synchronous and does not own named server calls.
    """
    import asyncio

    from agent_sandbox.api.sandbox import Sandbox

    async def _call() -> Any:
        sandbox = await Sandbox.connect(sandbox_id)
        try:
            return await sandbox.run(command, **args)
        finally:
            close = getattr(sandbox, "close", None)
            if callable(close):
                try:
                    await close()
                except Exception:
                    pass

    return asyncio.run(_call())


def _print_proc(label: str, proc: Proc) -> None:
    print(f"[{label}] exit {proc.returncode}", flush=True)
    text = scrub((proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else ""))
    tail = text.strip()[-2000:]
    if tail:
        print(tail, flush=True)


def save_intent(path: Path, intent: dict[str, Any]) -> None:
    """Persist only owned identifiers, never credentials or raw command output."""
    temporary = path.with_suffix(".new")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        json.dump(intent, stream)
        stream.write("\n")
    temporary.replace(path)


def official_templates(run: Runner, alias: str) -> list[str]:
    """Use the existing official CLI list API and exact unique-name matching."""
    proc = run(["--json", "template", "list", "--official-api"], 120)
    if proc.returncode:
        raise RuntimeError("official template reconciliation failed")
    data = json.loads(proc.stdout)
    if isinstance(data, dict) and data.get("status") == "success" and str(data.get("message", "")).startswith("No official templates found"):
        return []
    if not isinstance(data, list) or any(not isinstance(item, dict) for item in data):
        raise RuntimeError("unexpected official template list response")
    found = []
    for item in data:
        if alias not in {item.get("Name"), item.get("Alias")}:
            continue
        identifier = item.get("TemplateID")
        if not isinstance(identifier, str) or identifier.strip() in {"", "N/A"}:
            raise RuntimeError("matching official template has no valid ID")
        found.append(identifier)
    return found


def _list_owned_sandboxes(template_ids: set[str], known: set[str]) -> set[str]:
    """Read every page; matching exact recorded IDs/templates is not a prefix scan."""
    import asyncio
    from agent_sandbox.api.sandbox import Sandbox

    async def listing() -> set[str]:
        found: set[str] = set()
        offset = 0
        while True:
            rows = await Sandbox.list(provider="alicloud-express", limit=100, offset=offset)
            for row in rows:
                if (not isinstance(row.template, str) or not row.template.strip() or
                    not isinstance(row.sandbox_id, str) or not row.sandbox_id.strip()):
                    raise RuntimeError("unexpected sandbox list element shape")
                if row.template in template_ids or row.sandbox_id in known:
                    found.add(row.sandbox_id)
            if len(rows) < 100:
                return found
            offset += len(rows)

    return asyncio.run(asyncio.wait_for(listing(), 90))


def _recover_sandboxes(template_ids: set[str], known: set[str]) -> set[str]:
    import asyncio
    from agent_sandbox.api.sandbox import Sandbox

    found = _list_owned_sandboxes(template_ids, known)
    async def kill() -> None:
        for sandbox_id in found:
            await Sandbox.kill_by_id(sandbox_id, provider="alicloud-express")
    asyncio.run(asyncio.wait_for(kill(), 180))
    if _list_owned_sandboxes(template_ids, known):
        raise RuntimeError("owned sandboxes remain listed after kill")
    return found


def owned_resources_absent(intent: dict[str, Any], run: Runner) -> bool:
    """Independent readback is required even after CLI cleanup acknowledgement."""
    if official_templates(run, intent["alias"]):
        return False
    return not _list_owned_sandboxes(set(intent["template_ids"]), set(intent["sandbox_ids"]))


def template_state(payload: dict[str, Any]) -> str:
    """Read native status and the older CLI's Python-dict string formatting."""
    state = payload.get("status", payload.get("Status", ""))
    if isinstance(state, str) and state.startswith("{"):
        if len(state) > 4096:
            raise ValueError("oversized template state")
        try:
            state = json.loads(state)
        except json.JSONDecodeError:
            state = ast.literal_eval(state)
    if isinstance(state, dict):
        state = state.get("state", "")
    if not isinstance(state, str):
        raise ValueError("unexpected template state")
    return state.lower()


def wait_for_steps_ready(template_id: str, options: Options, run: Runner,
                         diagnostic_path: Path | None = None) -> bool:
    """submitted is not acceptance: independently poll official GetTemplate."""
    deadline = time.monotonic() + options.deploy_timeout
    while time.monotonic() < deadline:
        proc = run(["--json", "template", "info", template_id, "--official-api"],
                   min(120, max(1, deadline - time.monotonic())))
        payload = _last_json(proc)
        if diagnostic_path is not None:
            save_intent(diagnostic_path, {"exit_code": proc.returncode, "payload": payload})
        if proc.returncode or not payload:
            return False
        state = template_state(payload)
        if state == "ready":
            return True
        if state in {"error", "failed", "failure", "cancelled", "canceled"}:
            return False
        if state not in {"submitted", "pending", "building", "creating", "initializing", "processing"}:
            return False
        time.sleep(min(2, max(0, deadline - time.monotonic())))
    return False


def recover_owned(intent: dict[str, Any], run: Runner) -> bool:
    """Fail closed on an unknown create; never signal/delete by a broad prefix."""
    alias = intent.get("alias")
    if not isinstance(alias, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,62}", alias):
        raise ValueError("invalid owned alias")
    if intent.get("ownership_confirmed") is not True:
        return not intent.get("deploy_attempted")
    if not intent.get("deploy_attempted"):
        return True
    current = set(official_templates(run, alias))
    template_ids = set(intent.get("template_ids", [])) | current
    if not template_ids:
        print("BLOCKED unknown deployment response; exact owned intent retained", flush=True)
        return False
    if intent.get("create_attempted"):
        known = set(intent.get("sandbox_ids", []))
        found = _recover_sandboxes(template_ids, known)
        if not known and not found:
            print("BLOCKED unknown create response; absence is not proof of cancellation", flush=True)
            return False
        intent["sandbox_ids"] = sorted(known | found)
    intent["template_ids"] = sorted(template_ids)
    for template_id in current:
        proc = run(["template", "delete", template_id, "-y"], 120)
        if proc.returncode:
            return False
    return not official_templates(run, alias)


def execute(options: Options, *, runner: Runner | None = None, sdk: Sdk | None = None,
            verify: Callable[[dict[str, Any], Runner], bool] | None = None) -> int:
    if options.plan:
        print(json.dumps(plan_document(options), indent=2, ensure_ascii=False))
        return 0

    run = runner or default_runner
    call_sdk = sdk or default_sdk
    template_id: str | None = None
    sandbox_id: str | None = None
    blocked: tuple[str, str] | None = None
    results: list[dict[str, Any]] = []
    marker = options.template_dir / "Dockerfile.abx-build"
    marker_existed = marker.exists()

    def note_blocker(text: str) -> bool:
        nonlocal blocked
        found = classify_blocker(text)
        if found and blocked is None:
            blocked = found
        return found is not None

    if options.build_mode == "image":
        try:
            try:
                from .ci_image import validate_proof
            except ImportError:
                from ci_image import validate_proof
            validate_proof(options.template_dir, options.image_provenance, options.image_ref)
        except (ValueError, OSError):
            print("BLOCKED image source/provenance validation failed", flush=True)
            return 2
    intent_dir = Path(tempfile.mkdtemp(prefix="abx-express-owned-"))
    intent_path = intent_dir / "intent.json"
    intent = {"version": 1, "alias": options.alias,
              "acr_repo": options.alias if options.build_mode == "dockerfile" else None,
              "acr_tag": OWNED_ACR_TAG if options.build_mode == "dockerfile" else None,
              "template_ids": [], "sandbox_ids": [],
              "deploy_attempted": False, "create_attempted": False, "ownership_confirmed": False}
    save_intent(intent_path, intent)
    def conduct() -> int:
        nonlocal template_id, sandbox_id
        if runner is None and not os.environ.get("ABX") and not _which("abx"):
            print("ABX is not set and abx is not on PATH", file=sys.stderr)
            return 1
        deploy_args = [
            "--json",
            "template",
            "deploy",
            str(options.template_dir),
            "-y",
            "--generation",
            str(options.generation),
            "--start-cmd",
            options.start_cmd,
            "--ready-cmd",
            options.ready_cmd,
            "--alias",
            options.alias,
            "--build",
            options.build_mode,
            "--timeout",
            str(options.deploy_timeout),
            "--verbose",
        ]
        if options.build_mode == "image":
            username = os.environ.get("ABX_IMAGE_REGISTRY_USERNAME", "")
            password = os.environ.get("ABX_IMAGE_REGISTRY_PASSWORD", "")
            if not username or not password:
                print("BLOCKED explicit temporary image registry credentials are missing", flush=True)
                return 2
            if image_digest(options.image_ref) != options.image_provenance["pushed_image_digest"]:
                raise RuntimeError("image tag differs from checked archive digest before registration")
            config = _load_yaml(options.template_dir)
            resources = config.get("resources", {})
            deploy_args = ["--json", "template", "create", options.image_ref,
                "--name", options.alias, "--generation", str(options.generation),
                "--start-cmd", options.start_cmd, "--ready-cmd", options.ready_cmd,
                "--cpu", str(resources.get("cpu", 2)), "--memory", str(resources.get("memory", 2048)),
                "--no-envd-inject", "--registry-type", "acr",
                "--registry-username=" + username, "--registry-password=" + password]
        if options.build_mode == "dockerfile":
            deploy_args += ["--acr-repo", intent["acr_repo"], "--tag", intent["acr_tag"]]
        intent["deploy_attempted"] = True
        save_intent(intent_path, intent)
        print(
            f"deploy alias={options.alias} generation={options.generation} "
            f"lock={acr_lock_path()} idle={options.idle_timeout}s wall={options.wall_timeout}s",
            flush=True,
        )
        if runner is None and options.build_mode == "dockerfile":
            with acr_push_lock():
                deployed = _deploy_with_retries(options, deploy_args, None)
        else:
            deployed = _deploy_with_retries(options, deploy_args, run)
        _print_proc("deploy", deployed)
        payload = _last_json(deployed)
        if isinstance(payload, dict):
            raw_id = str(payload.get("TemplateID") or payload.get("templateID") or "").strip()
            if raw_id and raw_id != "N/A":
                template_id = raw_id
                intent["template_ids"] = [template_id]
                save_intent(intent_path, intent)
        combined = deployed.stdout + "\n" + deployed.stderr
        if deployed.returncode != 0 or not template_id:
            note_blocker(combined)
            if blocked:
                print(f"BLOCKED {blocked[0]} {blocked[1]}", flush=True)
                return 2
            print("deploy did not return a template id", flush=True)
            return 1
        status = template_state(payload or {})
        if options.build_mode == "image" or options.build_mode == "steps" and status == "submitted":
            if not wait_for_steps_ready(template_id, options, run, intent_dir / "readiness.json"):
                print("image registration did not independently reach READY" if options.build_mode == "image" else "step build did not independently reach READY", flush=True)
                return 1
            status = "ready"
        if status and status not in {"ready", "success", "succeeded"}:
            print(f"deploy status {status!r} is not READY", flush=True)
            note_blocker(combined)
            return 2 if blocked else 1

        intent["create_attempted"] = True
        save_intent(intent_path, intent)
        if options.sandbox_create == "sdk":
            try:
                known_id = default_sdk_create(template_id, options.sandbox_timeout)
                created = Proc(0, json.dumps({"ID": known_id}), "")
            except Exception as exc:
                # A failed request can have created a sandbox; keep the existing
                # unknown-create reconciliation and never publish its details.
                created = Proc(1, "", type(exc).__name__ + "; SDK creation response unavailable")
        else:
            created = run(
                ["--json", "create", "--template", template_id, "-y", "--timeout", str(options.sandbox_timeout)],
                420,
            )
        _print_proc("create", created)
        created_payload = _last_json(created)
        if isinstance(created_payload, dict):
            sandbox_id = str(created_payload.get("ID") or created_payload.get("id") or "").strip() or None
            if sandbox_id:
                intent["sandbox_ids"] = [sandbox_id]
                save_intent(intent_path, intent)
        if created.returncode != 0 or not sandbox_id:
            text = created.stdout + "\n" + created.stderr
            note_blocker(text)
            if blocked:
                print(f"BLOCKED {blocked[0]} {blocked[1]}", flush=True)
                return 2
            print("create did not return a sandbox id", flush=True)
            return 1

        passed = True
        for item in options.smoke:
            for via in ("cli", "sdk"):
                started = time.monotonic()
                ok = False
                observed: Any = None
                error = ""
                try:
                    if via == "cli":
                        proc = run(
                            ["--json", "run", sandbox_id, item.command, *_cli_args(item)],
                            180,
                        )
                        _print_proc(f"cli {item.command}", proc)
                        body = _last_json(proc)
                        if isinstance(body, dict) and "result" in body:
                            observed = body["result"]
                        else:
                            observed = proc.stdout.strip()
                        ok = proc.returncode == 0 and _matches(observed, item.expect)
                        if not ok:
                            error = scrub(proc.stderr or proc.stdout)[-500:]
                            note_blocker(proc.stdout + "\n" + proc.stderr)
                    else:
                        observed = call_sdk(sandbox_id, item.command, dict(item.args))
                        ok = _matches(observed, item.expect)
                        if not ok:
                            error = f"result {observed!r} != {item.expect!r}"
                except Exception as exc:  # noqa: BLE001 - recorded, then cleanup
                    error = scrub(f"{type(exc).__name__}: {exc}")[-500:]
                    note_blocker(error)
                    ok = False
                duration = round(time.monotonic() - started, 3)
                record: dict[str, Any] = {
                    "name": item.command,
                    "via": via,
                    "ok": ok,
                    "duration_s": duration,
                }
                if item.args:
                    record["args"] = item.args
                if ok:
                    record["result"] = observed if isinstance(observed, (str, int, float, bool, type(None))) else str(observed)
                elif error:
                    record["error"] = error
                results.append(record)
                print(f"[{'PASS' if ok else 'FAIL'}] {via} {item.command} {duration}s", flush=True)
                if not ok and error:
                    print(scrub(error), flush=True)
                if not ok:
                    passed = False

        if passed and not blocked:
            if options.build_mode == "image":
                if image_digest(options.image_ref) != options.image_provenance["pushed_image_digest"]:
                    raise RuntimeError("image tag changed during runtime acceptance")
                options.image_provenance["tag_digest_verified_after_runtime"] = True
            return 0
        if blocked:
            print(f"BLOCKED {blocked[0]} {blocked[1]}", flush=True)
            return 2
        print("smoke failed; evidence was not written", flush=True)
        return 1

    status = 1
    cleanup_ok = False
    try:
        # Refuse a pre-existing alias before the CLI can update that template.
        if official_templates(run, options.alias):
            print("BLOCKED deploy alias already exists; no owned cloud action attempted", flush=True)
            return 2
        intent["ownership_confirmed"] = True
        save_intent(intent_path, intent)
        status = conduct()
    except Exception as exc:
        print(f"harness operation failed: {type(exc).__name__}; upstream details omitted", flush=True)
        status = 1
    finally:
        uncertain = (intent["deploy_attempted"] and not template_id) or (intent["create_attempted"] and not sandbox_id)
        if intent["ownership_confirmed"] and intent["deploy_attempted"]:
            try:
                stop_deploy_processes(options.alias)
                if not uncertain:
                    cleanup_ok = _cleanup(run, sandbox_id, template_id, marker, marker_existed)
                    if cleanup_ok:
                        cleanup_ok = (verify or owned_resources_absent)(intent, run)
                        intent["readback_confirmed"] = cleanup_ok
            except Exception as exc:
                cleanup_ok = False
                print(f"owned cleanup failed: {type(exc).__name__}", flush=True)
        else:
            # A refused/failed read-only preflight establishes no ownership of
            # similarly named pushes or a concurrently generated build marker.
            cleanup_ok = True
        if uncertain or not cleanup_ok:
            try:
                intent["recovery_complete"] = recover_owned(intent, run)
            except Exception as exc:
                intent["recovery_complete"] = False
                print(f"owned recovery failed: {type(exc).__name__}; intent retained", flush=True)
            cleanup_ok = False  # The failed/ambiguous attempt never becomes provider-pass evidence.
        intent["cleanup_complete"] = cleanup_ok
        intent["result"] = "PASS" if status == 0 and cleanup_ok else "FAIL"
        save_intent(intent_path, intent)
        if status == 0 and cleanup_ok:
            _write_evidence(options, results)
            (intent_dir / "readiness.json").unlink(missing_ok=True)
            intent_path.unlink()
            intent_dir.rmdir()
        else:
            print(f"owned intent retained at {intent_path}; recover with --recover-intent", flush=True)
    return status if status else int(not cleanup_ok)


def _which(name: str) -> str | None:
    from shutil import which

    return which(name)


def _write_evidence(options: Options, results: list[dict[str, Any]]) -> None:
    now = datetime.now(timezone.utc)
    date = now.date().isoformat()
    directory = options.template_dir / "evidence"
    directory.mkdir(parents=True, exist_ok=True)
    payload = {
        "provider": "alicloud-express",
        "date": date,
        "template": options.template_name,
        "template_version": options.template_version,
        "sdk_version": _sdk_version(),
        "cli": "abx",
        "build_mode": options.build_mode,
        "sandbox_create": "python-sdk-Sandbox.create" if options.sandbox_create == "sdk" else "abx create",
        "harness_sha256": HARNESS_SHA256,
        "passed": True,
        "cleanup_verified": True,
        "commands": results,
    }
    provenance = options.template_dir / "steps-provenance.json"
    if options.build_mode == "steps" and provenance.is_file():
        payload["build_provenance"] = json.loads(provenance.read_text())
    if options.build_mode == "image":
        payload["image_provenance"] = options.image_provenance
        payload["registration_operation"] = "abx template create"
        payload["boundary"] = "Verified CI Dockerfile image + private registry transfer; no controller Docker build or platform-step build claimed"
    # Template ids are ephemeral and must not be stored.
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if classify_blocker(text):
        raise RuntimeError("refusing to write evidence that matches a known failure")
    path = directory / f"express-{date}.json"
    if path.exists():
        raise RuntimeError("refusing to overwrite an existing acceptance receipt; use a fresh staging directory")
    path.write_text(text, encoding="utf-8")
    print(f"evidence {path}", flush=True)


def _cleanup(
    run: Runner,
    sandbox_id: str | None,
    template_id: str | None,
    marker: Path,
    marker_existed: bool,
) -> bool:
    ok = True
    if sandbox_id:
        try:
            proc = run(["kill", sandbox_id, "-y"], 90)
            _print_proc("kill", proc)
            if proc.returncode:
                ok = False
        except Exception as exc:  # noqa: BLE001
            print(f"kill failed: {type(exc).__name__}", flush=True)
            ok = False
    if template_id and ok:
        try:
            proc = run(["template", "delete", template_id, "-y"], 90)
            _print_proc("template delete", proc)
            if proc.returncode:
                ok = False
        except Exception as exc:  # noqa: BLE001
            print(f"template delete failed: {type(exc).__name__}", flush=True)
            ok = False
    if marker.exists() and not marker_existed:
        marker.unlink()
    return ok


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments[:1] == ["--recover-intent"]:
        if len(arguments) != 2:
            raise SystemExit("usage: express_e2e.py --recover-intent PRIVATE_PATH")
        path = Path(arguments[1])
        if path.is_symlink() or not path.is_file() or path.stat().st_uid != os.getuid() or path.stat().st_mode & 0o077:
            raise SystemExit("owned intent must be a private regular file owned by this user")
        intent = json.loads(path.read_text())
        try:
            complete = recover_owned(intent, default_runner)
        except Exception as exc:
            print(f"owned recovery failed: {type(exc).__name__}; intent retained", flush=True)
            return 2
        intent["recovery_complete"] = complete
        save_intent(path, intent)
        return 0 if complete else 2
    options = build_options(arguments)
    return execute(options)


if __name__ == "__main__":
    sys.exit(main())
