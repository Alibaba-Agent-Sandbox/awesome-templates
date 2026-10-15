#!/usr/bin/env python3
"""Deploy one template to Alibaba Cloud Express and run its smoke commands.

The harness reads ``generation``, ``start_cmd``, ``ready_cmd``, and ``smoke``
from ``template.yaml``. It deploys with ``abx template deploy`` (generation 2),
creates one sandbox, calls each smoke command through ``abx run`` and through
``await Sandbox.connect`` / ``await sb.run``, and always deletes that sandbox and that
template in a ``finally`` block.

A passing run writes ``<template>/evidence/express-<YYYY-MM-DD>.json``.
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
import fcntl
import json
import os
import re
import shlex
import signal
import subprocess
import sys
import threading
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


@dataclass
class Proc:
    returncode: int
    stdout: str
    stderr: str


Runner = Callable[[list[str], float], Proc]
Sdk = Callable[[str, str, dict[str, Any]], Any]

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
            code = proc.poll()
            now = time.monotonic()
            if code is not None:
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
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _kill_process_group(pgid)
            proc.wait(timeout=5)
    finally:
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
    )


def plan_document(options: Options) -> dict[str, Any]:
    return {
        "template": str(options.template_dir),
        "name": options.template_name,
        "version": options.template_version,
        "alias": options.alias,
        "generation": options.generation,
        "start_cmd": options.start_cmd,
        "ready_cmd": options.ready_cmd,
        "deploy_timeout": options.deploy_timeout,
        "idle_timeout": options.idle_timeout,
        "wall_timeout": options.wall_timeout,
        "push_retries": options.push_retries,
        "acr_push_lock": str(acr_lock_path()),
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
    attempts = options.push_retries + 1
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


def default_sdk(sandbox_id: str, command: str, args: dict[str, Any]) -> Any:
    """Call one named command.

    ``Sandbox.connect_sync`` / ``create_sync`` on python-sdk 0.3.0 drop the
    class argument (``TypeError: missing sandbox_id``). The async methods are
    the ones that work.
    """
    import asyncio

    from agent_sandbox import Sandbox

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


def execute(options: Options, *, runner: Runner | None = None, sdk: Sdk | None = None) -> int:
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

    try:
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
            "--acr-repo",
            options.alias,
            "--tag",
            options.alias.split("-")[-1],
            "--timeout",
            str(options.deploy_timeout),
            "--verbose",
        ]
        print(
            f"deploy alias={options.alias} generation={options.generation} "
            f"lock={acr_lock_path()} idle={options.idle_timeout}s wall={options.wall_timeout}s",
            flush=True,
        )
        if runner is None:
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
        combined = deployed.stdout + "\n" + deployed.stderr
        if deployed.returncode != 0 or not template_id:
            note_blocker(combined)
            if blocked:
                print(f"BLOCKED {blocked[0]} {blocked[1]}", flush=True)
                return 2
            print("deploy did not return a template id", flush=True)
            return 1
        status = str((payload or {}).get("Status") or (payload or {}).get("status") or "").lower()
        if status and status not in {"ready", "success", "succeeded"}:
            print(f"deploy status {status!r} is not READY", flush=True)
            note_blocker(combined)
            return 2 if blocked else 1

        created = run(
            ["--json", "create", "--template", template_id, "-y", "--timeout", "300"],
            420,
        )
        _print_proc("create", created)
        created_payload = _last_json(created)
        if isinstance(created_payload, dict):
            sandbox_id = str(created_payload.get("ID") or created_payload.get("id") or "").strip() or None
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
            _write_evidence(options, results)
            return 0
        if blocked:
            print(f"BLOCKED {blocked[0]} {blocked[1]}", flush=True)
            return 2
        print("smoke failed; evidence was not written", flush=True)
        return 1
    finally:
        try:
            stop_deploy_processes(options.alias)
        except Exception as exc:  # noqa: BLE001 - cleanup must not hide the deploy result
            print(f"deploy process cleanup failed: {scrub(str(exc))}", flush=True)
        _cleanup(run, sandbox_id, template_id, marker, marker_existed)


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
        "passed": True,
        "commands": results,
    }
    # Template ids are ephemeral and must not be stored.
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if classify_blocker(text):
        raise RuntimeError("refusing to write evidence that matches a known failure")
    path = directory / f"express-{date}.json"
    path.write_text(text, encoding="utf-8")
    print(f"evidence {path}", flush=True)


def _cleanup(
    run: Runner,
    sandbox_id: str | None,
    template_id: str | None,
    marker: Path,
    marker_existed: bool,
) -> None:
    if sandbox_id:
        try:
            proc = run(["kill", sandbox_id, "-y"], 90)
            _print_proc("kill", proc)
        except Exception as exc:  # noqa: BLE001
            print(f"kill failed: {scrub(str(exc))}", flush=True)
    if template_id:
        try:
            proc = run(["template", "delete", template_id, "-y"], 90)
            _print_proc("template delete", proc)
        except Exception as exc:  # noqa: BLE001
            print(f"template delete failed: {scrub(str(exc))}", flush=True)
    if marker.exists() and not marker_existed:
        marker.unlink()


def main(argv: list[str] | None = None) -> int:
    options = build_options(argv)
    return execute(options)


if __name__ == "__main__":
    sys.exit(main())
