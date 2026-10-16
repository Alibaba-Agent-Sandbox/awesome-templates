"""Explicitly authorized canonical Express acceptance; no credentials are stored.

No raw cloud/CLI log or private journal is an upload artifact. This controller
runs the real canonical harness, never a copied deploy implementation.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
from email.utils import format_datetime
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import shlex
import signal
import selectors
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

TEMPLATES = ("agents-cli", "amp", "browser-automation", "claude-code", "codex",
    "codex-agent-api", "deepseek-harness", "droid", "gemini", "hermes-agent",
    "node-web", "openclaw", "opencode", "pi", "python-hello", "qoder", "qwen-code")
PINS = {"templates": "a361f490555ead0ff67081ffb4874abf292a1b2f",
        "harness": "1c4bbdd3d9596b65cdded6a611f8d28e7580a45e",
        "cli": "37b6d276bdca875811ce7fb0ae88aca64882fcaa",
        "controller": "666657b5706945d8899061033edc09b6eb2af953",
        "server": "e2cb27e24fde0a67112f82b8d44af463445a5d1a"}
REQUIRED = ("ALICLOUD_ACCESS_KEY_ID", "ALICLOUD_ACCESS_KEY_SECRET", "ACR_NAMESPACE",
            "ABX_SANDBOX_API_KEY", "ABX_SANDBOX_BASE_URL", "ABX_SANDBOX_DOMAIN")


def save(path: Path, data: dict, *, private: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".new")
    temporary.write_text(json.dumps(data, indent=2) + "\n")
    if private:
        temporary.chmod(0o600)
    temporary.replace(path)


def select(text: str) -> list[str]:
    names = list(TEMPLATES) if text == "all" else text.split(",")
    if not names or len(set(names)) != len(names) or any(name not in TEMPLATES for name in names):
        raise ValueError("select unique reviewed template names or all")
    return names


def authorization(env: dict[str, str]) -> tuple[bool, list[str]]:
    names = select(env.get("REVIEW_TEMPLATES", "python-hello"))
    head = env.get("REVIEW_HEAD", "")
    enabled = (env.get("REVIEW_ENABLE") == "approved" and
               re.fullmatch(r"[0-9a-f]{40}", head) is not None and
               env.get("REVIEW_APPROVED_SHA") == head and
               env.get("REVIEW_SAME_REPOSITORY") == "true")
    return enabled, names


def plan() -> int:
    enabled, names = authorization(dict(os.environ))
    save(Path("canonical-authorization.json"), {"result": "AUTHORIZED" if enabled else "BLOCKED",
        "cloud_executed": False, "reason": "exact-head opt-in accepted" if enabled else
        "default disabled, unapproved workflow head or fork; no cloud acceptance",
        "templates": names, "source_pins": PINS})
    with open(os.environ["GITHUB_OUTPUT"], "a") as stream:
        stream.write("enabled=" + str(enabled).lower() + "\n")
        stream.write("templates=" + json.dumps(names) + "\n")
    print("AUTHORIZED cloud preparation" if enabled else "BLOCKED: no cloud execution authorized", flush=True)
    return 0  # The artifact says BLOCKED; this is not an L2 pass check.


def registry(method: str, path: str) -> None:
    """Official ACR 2016-06-07 ROA DeleteImage/DeleteRepo/GetRepo paths."""
    headers = {"Accept": "application/json", "Content-Type": "application/json",
        "Date": format_datetime(datetime.now(timezone.utc), usegmt=True),
        "x-acs-signature-method": "HMAC-SHA1", "x-acs-signature-nonce": str(uuid.uuid4()),
        "x-acs-signature-version": "1.0", "x-acs-version": "2016-06-07"}
    canonical = "".join(k + ":" + headers[k] + "\n" for k in sorted(headers) if k.startswith("x-acs-"))
    signed = method + "\napplication/json\n\napplication/json\n" + headers["Date"] + "\n" + canonical + path
    signature = base64.b64encode(hmac.new(os.environ["ALICLOUD_ACCESS_KEY_SECRET"].encode(), signed.encode(), hashlib.sha1).digest()).decode()
    headers["Authorization"] = "acs " + os.environ["ALICLOUD_ACCESS_KEY_ID"] + ":" + signature
    request = urllib.request.Request("https://cr.cn-hangzhou.aliyuncs.com" + path, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            response.read()
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise FileNotFoundError("owned registry object absent") from None
        raise RuntimeError("ACR API HTTP " + str(exc.code)) from None


def delete_absent(path: str) -> None:
    try:
        registry("DELETE", path)
    except FileNotFoundError:
        pass
    for attempt in range(15):
        try:
            registry("GET", path)
        except FileNotFoundError:
            return
        time.sleep(2)
    raise RuntimeError("owned registry deletion not confirmed")


def private_root(template: str) -> Path:
    return Path(os.environ["RUNNER_TEMP"]) / ("canonical-express-" + template)


def child_environment(private: Path) -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if key in REQUIRED or key in
        {"PATH", "HOME", "LANG", "LC_ALL", "SSL_CERT_FILE", "SSL_CERT_DIR", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE", "HTTPS_PROXY",
         "HTTP_PROXY", "ALL_PROXY", "NO_PROXY", "https_proxy", "http_proxy", "all_proxy", "no_proxy"}}
    env.update({"ALIBABA_CLOUD_REGION_ID": "cn-hangzhou", "ABX_ENGINE_INPROCESS": "1",
        "ABX_ENGINE_SOCKET": str(private / "engine.sock"), "DOCKER_CONFIG": str(private / "docker"),
        "TMPDIR": str(private / "tmp"), "ABX_BASE_IMAGE_TAG": "v0.0.49",
        "ABX_SERVER_SDK_SOURCE": str(Path("reviewed/server/server-sdk").resolve()),
        "ABX": shlex.join(["node", str(Path("reviewed/cli/dist/bin/abx.js").resolve())])})
    return env


def invoke(argv: list[str], env: dict[str, str], *, timeout: int, _grace: float = 300) -> int:
    """Discard diagnostics; keep the owned leader unreaped until group cleanup."""
    process = subprocess.Popen(argv, env=env, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    pipes = selectors.DefaultSelector()
    for stream in (process.stdout, process.stderr):
        os.set_blocking(stream.fileno(), False)
        pipes.register(stream, selectors.EVENT_READ)
    deadline = time.monotonic() + timeout
    timed_out = False
    try:
        while True:
            # WNOWAIT reserves the leader PID and therefore its process-group
            # identity until the final killpg, including successful exits.
            exited = os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
            if exited is not None:
                break
            if time.monotonic() >= deadline:
                if timed_out:
                    break
                timed_out = True
                os.kill(process.pid, signal.SIGINT)  # Allow canonical finally.
                deadline = time.monotonic() + _grace
            for key, _ in pipes.select(0.05):
                chunk = os.read(key.fd, 65536)
                if not chunk:
                    pipes.unregister(key.fileobj)
        if timed_out:
            return 124
        result = os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOWAIT)
        return result.si_status if result.si_code == os.CLD_EXITED else -result.si_status
    finally:
        # The leader has never been reaped, so this cannot target a reused PGID.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=5)
        pipes.close()
        process.stdout.close()
        process.stderr.close()


def finish(template: str) -> int:
    private = private_root(template)
    state_path = private / "state.json"
    output = Path("canonical-output") / template
    if not state_path.exists():
        # Earlier setup/preflight may have failed; never invent an acceptance.
        save(output / "status.json", {"result": "BLOCKED", "template": template,
            "cloud_executed": False, "reason": "no owned run state was created"})
        return 2
    state = json.loads(state_path.read_text())
    env = child_environment(private)
    cleanup_ok = True
    for intent in (private / "tmp").glob("abx-express-owned-*/intent.json"):
        if invoke([sys.executable, "reviewed/harness/scripts/express_e2e.py",
                   "--recover-intent", str(intent)], env, timeout=360) != 0:
            cleanup_ok = False
    if cleanup_ok and state.get("registry_owned"):
        try:
            if state.get("acr_repo") != state["alias"] or state.get("acr_tag") != "review":
                raise RuntimeError("owned registry intent mapping differs from the canonical runner")
            path = "/repos/" + urllib.parse.quote(os.environ["ACR_NAMESPACE"], safe="") + "/" + state["acr_repo"]
            delete_absent(path + "/tags/" + state["acr_tag"])
            delete_absent(path)
            state["registry_owned"] = False
        except Exception:
            cleanup_ok = False
    state["cleanup_confirmed"] = cleanup_ok
    passed = state.get("canonical_exit") == 0 and cleanup_ok and state.get("canonical_evidence_checked") is True
    status = {"result": "PASS" if passed else "BLOCKED" if state.get("canonical_exit") == 2 else "FAIL", "template": template,
        "canonical_exit": state.get("canonical_exit"), "cleanup_confirmed": cleanup_ok,
        "stage": state.get("stage"), "error_category": state.get("error_category"),
        "source_pins": PINS, "models_called": False,
        "boundary": "canonical L2 smoke only; no image-backed L3 or full external HTTP suite"}
    if passed:
        candidate = Path(state["candidate"])
        output.mkdir(parents=True, exist_ok=True)
        (output / candidate.name).write_bytes(candidate.read_bytes())
    else:
        for evidence in output.glob("express-*.json"):
            evidence.unlink()
    save(output / "status.json", status)
    save(state_path, state, private=True)
    print(status["result"] + ": canonical Express " + template + "; cleanup=" + str(cleanup_ok), flush=True)
    return 0 if passed else 1


def run(template: str) -> int:
    output = Path("canonical-output") / template
    if not authorization(dict(os.environ))[0]:
        save(output / "status.json", {"result": "BLOCKED", "template": template,
            "cloud_executed": False, "reason": "explicit exact-head authorization is absent"})
        print("BLOCKED: execution authorization absent; no cloud calls", flush=True)
        return 2
    missing = [name for name in REQUIRED if not os.environ.get(name)]
    if missing:
        save(output / "status.json", {"result": "BLOCKED", "template": template,
            "cloud_executed": False, "missing_secret_names": missing})
        print("BLOCKED: missing required credential/configuration names; values omitted", flush=True)
        return 2
    for name, pin in PINS.items():
        actual = subprocess.check_output(["git", "-C", "reviewed/" + name, "rev-parse", "HEAD"], text=True).strip()
        if actual != pin:
            raise RuntimeError("reviewed source pin mismatch")
    private = private_root(template)
    private.mkdir(mode=0o700)
    (private / "tmp").mkdir(mode=0o700)
    (private / "docker").mkdir(mode=0o700)
    run_id, attempt = os.environ["GITHUB_RUN_ID"], os.environ["GITHUB_RUN_ATTEMPT"]
    if not run_id.isdigit() or not attempt.isdigit():
        raise ValueError("invalid GitHub run identity")
    alias = "e2e-gh-" + run_id + "-" + attempt + "-" + template
    if len(alias) > 63:
        raise ValueError("owned alias exceeds platform limit")
    state = {"alias": alias, "acr_repo": alias, "acr_tag": "review", "registry_owned": False, "canonical_exit": None}
    save(private / "state.json", state, private=True)
    try:
        state["stage"] = "registry ownership preflight"
        save(private / "state.json", state, private=True)
        repo_path = "/repos/" + urllib.parse.quote(os.environ["ACR_NAMESPACE"], safe="") + "/" + state["acr_repo"]
        try:
            registry("GET", repo_path)
        except FileNotFoundError:
            pass
        else:
            raise RuntimeError("owned registry name already exists; refusing mutation")
        state["registry_owned"] = True
        save(private / "state.json", state, private=True)
        source = Path("reviewed/templates") / template
        evidence_dir = source / "evidence"
        before = set(evidence_dir.glob("express-*.json"))
        today = evidence_dir / ("express-" + datetime.now(timezone.utc).date().isoformat() + ".json")
        if today.exists():
            raise RuntimeError("canonical source already contains today's evidence; refusing stale receipt")
        state["stage"] = "canonical deploy and CLI/SDK smoke"
        save(private / "state.json", state, private=True)
        code = invoke([sys.executable, "reviewed/harness/scripts/express_e2e.py", str(source),
            "--alias", alias, "--timeout", "900", "--idle-timeout", "300",
            "--wall-timeout", "3600", "--push-retries", "0"], child_environment(private), timeout=6000)
        state["canonical_exit"] = code
        if code == 0:
            state["stage"] = "canonical receipt validation"
            fresh = set(evidence_dir.glob("express-*.json")) - before
            if len(fresh) != 1:
                raise RuntimeError("expected exactly one fresh canonical receipt")
            candidate = fresh.pop()  # Also handles an accepted run crossing UTC midnight.
            data = json.loads(candidate.read_text())
            import yaml
            config = yaml.safe_load((source / "template.yaml").read_text())
            if (data["provider"] != "alicloud-express" or data["passed"] is not True or data.get("cleanup_verified") is not True or
                data["template"] != template or data["template_version"] != str(config["version"]) or
                data["cli"] != "abx" or candidate.name != "express-" + data["date"] + ".json" or
                not data["commands"] or not all(row["ok"] is True for row in data["commands"]) or
                not all({"cli", "sdk"} <= {row["via"] for row in data["commands"] if row["name"] == item["command"]} for item in config["smoke"])):
                raise RuntimeError("canonical receipt does not match the reviewed smoke scope")
            raw = candidate.read_text()
            for name in REQUIRED:
                value = os.environ[name]
                if any(variant in raw for variant in (value, json.dumps(value)[1:-1], json.dumps(value, ensure_ascii=False)[1:-1])):
                    raise RuntimeError("refusing a receipt containing configured private values")
            state.update({"canonical_evidence_checked": True, "candidate": str(candidate)})
    except Exception as exc:
        state["error_category"] = type(exc).__name__
    finally:
        save(private / "state.json", state, private=True)
    return finish(template)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("plan", "run", "cleanup"))
    parser.add_argument("--template", choices=TEMPLATES)
    args = parser.parse_args()
    if args.action == "plan":
        return plan()
    if not args.template:
        parser.error("--template is required")
    return run(args.template) if args.action == "run" else finish(args.template)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("FAIL: controller " + type(exc).__name__ + "; private details omitted", flush=True)
        raise SystemExit(1)
