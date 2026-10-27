"""Owned, bounded OpenClaw gateway lifecycle; no system-service or PID-file control."""
from __future__ import annotations

import atexit
import ipaddress
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import signal
import socket
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

from agent_sandbox.server import command, start

VERSION = "2026.10.4"
_LOCK = threading.RLock()
_PROCESS: subprocess.Popen | None = None
_STATE: tempfile.TemporaryDirectory | None = None
_ENV: dict[str, str] = {}
_PORT = 18789
_BIND = "loopback"


def _model_config() -> dict | None:
    names = ("OPENCLAW_MODEL_API_KEY", "OPENCLAW_MODEL_BASE_URL", "OPENCLAW_MODEL")
    values = [os.environ.get(name, "").strip() for name in names]
    if not any(values):
        return None
    if not all(values):
        raise ValueError("set OPENCLAW_MODEL_API_KEY, OPENCLAW_MODEL_BASE_URL and OPENCLAW_MODEL together")
    key, base_url, model = values
    parsed = urllib.parse.urlsplit(base_url)
    if (parsed.scheme not in {"http", "https"} or not parsed.hostname or
            parsed.username or parsed.password or parsed.query or parsed.fragment):
        raise ValueError("OPENCLAW_MODEL_BASE_URL must be an explicit HTTP(S) API base without credentials/query/fragment")
    if len(base_url) > 2048 or len(model) > 256 or any(c.isspace() for c in model):
        raise ValueError("invalid model endpoint or model identifier")
    return {"baseUrl": base_url.rstrip("/"), "apiKey": "${OPENCLAW_MODEL_API_KEY}",
            "api": "openai-completions", "models": [{"id": model, "name": model,
                "reasoning": False, "input": ["text"], "contextWindow": 128000, "maxTokens": 4096}]}


def _trusted_proxies() -> list[str]:
    raw = os.environ.get("OPENCLAW_TRUSTED_PROXIES", "").strip()
    if not raw:
        return []
    if len(raw.encode("utf-8")) > 2048:
        raise ValueError("OPENCLAW_TRUSTED_PROXIES exceeds its byte limit")
    values = raw.split(",")
    if len(values) > 16:
        raise ValueError("OPENCLAW_TRUSTED_PROXIES supports at most 16 explicit IPs/CIDRs")
    result = []
    for value in values:
        try:
            network = ipaddress.ip_network(value.strip(), strict=False)
        except ValueError:
            raise ValueError("OPENCLAW_TRUSTED_PROXIES requires explicit IPs/CIDRs") from None
        mapped_wildcard = (network.version == 6 and network.prefixlen <= 96
                           and ipaddress.ip_network("::ffff:0:0/96").subnet_of(network))
        if network.prefixlen == 0 or network.network_address.is_unspecified or network.is_multicast or mapped_wildcard:
            raise ValueError("OPENCLAW_TRUSTED_PROXIES refuses unrestricted or non-unicast networks")
        canonical = str(network)
        if canonical not in result:
            result.append(canonical)
    return result


def _validate(port: int, command_timeout: int) -> None:
    if not 1024 <= port <= 65535 or port == 9000:
        raise ValueError("port must be 1024..65535 and different from the server port 9000")
    if not 1 <= command_timeout <= 120:
        raise ValueError("command_timeout must be 1..120 seconds")


def _binary() -> str:
    executable = shutil.which("openclaw")
    if not executable:
        raise RuntimeError(f"openclaw@{VERSION} is not installed on PATH")
    return executable


def _running() -> bool:
    process = _PROCESS
    if process is None or process.returncode is not None:
        return False
    # Observe without reaping, including when the leader exits unexpectedly.
    # Its reserved PID remains our group identity anchor until _stop_owned.
    info = os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
    return info is None


def _live_group_members(group: int) -> bool:
    # Linux sandbox runtime. Keep the leader unreaped while inspecting group
    # members: even a zombie leader reserves its PID, preventing PGID reuse.
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            fields = (entry / "stat").read_text().rsplit(")", 1)[1].split()
            if int(fields[2]) == group and fields[0] != "Z":
                return True
        except (OSError, ValueError, IndexError):
            continue
    return False


def _stop_owned(command_timeout: int) -> None:
    global _PROCESS, _STATE, _ENV
    process = _PROCESS
    # No PID files. The unreaped owned leader is the process-group identity
    # anchor; never wait/poll it between TERM and the final group KILL.
    if process is not None and process.returncode is None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
            deadline = time.monotonic() + command_timeout
            while _live_group_members(process.pid) and time.monotonic() < deadline:
                time.sleep(0.05)
            # Kill the group before reaping the leader. This also catches a child
            # that ignored TERM after the leader exited, without a recycled-PID race.
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=5)
    _PROCESS = None
    _ENV = {}
    if _STATE is not None:
        _STATE.cleanup()
        _STATE = None


# Generated from scripts/process_runners/text.py; update with scripts/sync_process_runners.py.
def _run_process(argv: list[str], *, cwd: str, timeout: int | float,
                 env: dict | None = None, input_text: str | None = None) -> tuple[int, str, str]:
    """Keep the Linux session leader unreaped until its owned group is stopped."""
    process = subprocess.Popen(argv, cwd=cwd, env=env,
        stdin=subprocess.PIPE if input_text is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    stdout_parts: list[bytes] = []
    stderr_parts: list[bytes] = []
    def drain(stream, parts):
        try:
            while chunk := stream.read(65536):
                parts.append(chunk)
        except OSError:
            pass
        finally:
            stream.close()
    readers = [threading.Thread(target=drain, args=(process.stdout, stdout_parts), daemon=True),
               threading.Thread(target=drain, args=(process.stderr, stderr_parts), daemon=True)]
    for reader in readers:
        reader.start()
    if input_text is not None:
        def feed():
            try:
                process.stdin.write(input_text.encode())
                process.stdin.close()
            except (OSError, ValueError):
                pass
            finally:
                try:
                    process.stdin.close()
                except (OSError, ValueError):
                    pass
        threading.Thread(target=feed, daemon=True).start()
    deadline = time.monotonic() + timeout
    timed_out = False
    try:
        while os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is None:
            if time.monotonic() >= deadline:
                timed_out = True
                break
            time.sleep(0.02)
    finally:
        # WNOWAIT pins the original PID/PGID even after leader exit. No poll(),
        # wait() or communicate() may reap it before group cleanup.
        if timed_out:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            grace = time.monotonic() + 1
            while time.monotonic() < grace:
                if os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is not None:
                    break
                time.sleep(0.02)
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            raise RuntimeError("owned process cleanup timed out") from None
        for reader in readers:
            reader.join(timeout=2)
    if timed_out:
        raise RuntimeError(f"command timed out after {timeout} seconds") from None
    return (process.returncode, b"".join(stdout_parts).decode("utf-8", "replace"),
            b"".join(stderr_parts).decode("utf-8", "replace"))


def _probe(timeout: float) -> bool:
    if not _running():
        return False
    # The short-lived authenticated RPC has its own group. Clean it without
    # signalling the separately owned long-running gateway process group.
    argv = [_binary(), "gateway", "health", "--json", "--timeout", str(max(1, int(timeout * 1000)))]
    try:
        code, stdout, _ = _run_process(argv, cwd=os.getcwd(), timeout=timeout, env=_ENV)
    except RuntimeError:
        return False
    if code:
        return False
    try:
        return json.loads(stdout).get("ok") is True
    except (ValueError, AttributeError):
        return False


@command("gateway_start", description="Start an owned authenticated OpenClaw gateway and wait for health.")
def gateway_start(port: int = 18789, bind: str = "loopback", command_timeout: int = 60) -> dict:
    global _PROCESS, _STATE, _ENV, _PORT, _BIND
    _validate(port, command_timeout)
    if bind not in ("loopback", "lan"):
        raise ValueError("bind must be loopback or lan")
    if not os.environ.get("OPENCLAW_GATEWAY_TOKEN", "").strip():
        raise RuntimeError("OPENCLAW_GATEWAY_TOKEN is required; inject it in the sandbox environment")
    with _LOCK:
        if _running():
            if port != _PORT or bind != _BIND:
                raise RuntimeError("an owned gateway is already running; stop it before changing port or bind")
            if not _probe(min(command_timeout, 20)):
                raise RuntimeError("owned gateway is running but its authenticated health check failed")
            return {"running": True, "healthy": True, "url": f"ws://127.0.0.1:{port}", "bind": bind}
        _stop_owned(1)
        # Refuse port conflicts instead of --force, which could kill another process.
        with socket.socket() as check:
            # Node's server may leave accepted connections in TIME_WAIT after
            # owned shutdown. Match its reusable listener semantics; an active
            # foreign listener still prevents bind and is never signalled.
            check.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                check.bind(("0.0.0.0" if bind == "lan" else "127.0.0.1", port))
            except OSError:
                raise RuntimeError("gateway port is already occupied; choose another port") from None
        executable = _binary()
        trusted_proxies = _trusted_proxies()
        model_config = _model_config()
        _STATE = tempfile.TemporaryDirectory(prefix="abx-openclaw-")
        state = Path(_STATE.name)
        config = {"gateway": {"mode": "local", "port": port, "bind": bind,
                  "auth": {"mode": "token", "token": "${OPENCLAW_GATEWAY_TOKEN}"},
                  "controlUi": {"enabled": False}},
                  "browser": {"enabled": False}}
        if model_config:
            config["gateway"]["http"] = {"endpoints": {"chatCompletions": {"enabled": True}}}
            config["models"] = {"mode": "replace", "providers": {"abx": model_config}}
            config["agents"] = {"defaults": {"model": {"primary": "abx/" + model_config["models"][0]["id"]},
                "workspace": str(state / "workspace")}}
            config["tools"] = {"profile": "minimal", "deny": ["*"]}
        if trusted_proxies:
            config["gateway"]["trustedProxies"] = trusted_proxies
        (state / "openclaw.json").write_text(json.dumps(config), encoding="utf-8")
        _ENV = os.environ.copy()
        _ENV.update(OPENCLAW_STATE_DIR=str(state), OPENCLAW_CONFIG_PATH=str(state / "openclaw.json"),
                    OPENCLAW_NO_RESPAWN="1", OPENCLAW_SKIP_CHANNELS="1")
        _PORT, _BIND = port, bind
        try:
            _PROCESS = subprocess.Popen(
                [executable, "gateway", "run", "--allow-unconfigured", "--bind", bind,
                 "--auth", "token", "--port", str(port)],
                env=_ENV, cwd=state, stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            deadline = time.monotonic() + command_timeout
            while time.monotonic() < deadline:
                if not _running():
                    raise RuntimeError("OpenClaw gateway exited before authenticated readiness")
                if _probe(min(15, max(0.1, deadline - time.monotonic()))):
                    return {"running": True, "healthy": True,
                            "url": f"ws://127.0.0.1:{port}", "bind": bind}
                time.sleep(min(0.25, max(0, deadline - time.monotonic())))
            raise RuntimeError("OpenClaw gateway did not become healthy before timeout")
        except BaseException:
            _stop_owned(2)
            raise


@command("gateway_status", description="Inspect this server's owned gateway without claiming health.")
def gateway_status() -> dict:
    with _LOCK:
        running = _running()
        return {"running": running, "owned": running,
                "url": f"ws://127.0.0.1:{_PORT}" if running else None}


@command("gateway_health", description="Run an authenticated gateway health RPC; fail if unhealthy.")
def gateway_health(command_timeout: int = 20) -> dict:
    _validate(_PORT, command_timeout)
    with _LOCK:
        if not _probe(command_timeout):
            raise RuntimeError("owned gateway is absent or authenticated health check failed")
        return {"healthy": True, "url": f"ws://127.0.0.1:{_PORT}"}


@command("gateway_chat", description="Send a text turn through the owned native gateway; reuse session_id for context.")
def gateway_chat(prompt: str, session_id: str = "", command_timeout: int = 180) -> dict:
    if not prompt.strip() or len(prompt.encode("utf-8")) > 65536:
        raise ValueError("prompt must contain 1..65536 UTF-8 bytes")
    if not 1 <= command_timeout <= 300:
        raise ValueError("command_timeout must be 1..300 seconds")
    if session_id and not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", session_id):
        raise ValueError("session_id must contain 1..80 ASCII letters, digits, underscores or hyphens")
    with _LOCK:
        if _model_config() is None:
            raise RuntimeError("gateway_chat requires the three explicit OPENCLAW_MODEL settings")
        if not _running():
            gateway_start()
        conversation = session_id or secrets.token_hex(16)
        payload = {"model": "openclaw/default", "user": "abx-conversation:" + conversation,
                   "messages": [{"role": "user", "content": prompt}], "stream": False}
        request = urllib.request.Request(f"http://127.0.0.1:{_PORT}/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json",
            "Authorization": "Bearer " + _ENV["OPENCLAW_GATEWAY_TOKEN"]})
        # Local gateway traffic never goes through a caller's external proxy.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            with opener.open(request, timeout=command_timeout) as response:
                raw = response.read(1048577)
            if len(raw) > 1048576:
                raise RuntimeError("gateway response exceeds 1 MiB")
            result = json.loads(raw)
            text = result["choices"][0]["message"]["content"]
            if not isinstance(text, str) or not text.strip():
                raise ValueError("empty assistant response")
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"native gateway chat failed with HTTP {exc.code}") from None
        except (OSError, ValueError, KeyError, IndexError, TypeError):
            raise RuntimeError("native gateway chat failed or returned no assistant text") from None
        return {"session_id": conversation, "text": text}


@command("gateway_stop", description="Stop only the gateway owned by this server process.")
def gateway_stop(command_timeout: int = 10) -> dict:
    _validate(_PORT, command_timeout)
    with _LOCK:
        _stop_owned(command_timeout)
        return {"running": False, "owned": False}


atexit.register(_stop_owned, 2)

if __name__ == "__main__":
    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
