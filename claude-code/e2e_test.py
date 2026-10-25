#!/usr/bin/env python3
"""End-to-end test suite for the ``claude-code`` template.

Exercises built-in routes (/health, /commands), the registered ``claude``
command (Claude Code CLI), FILE_OPS file round-trip, PROCESS shell/process
control and the TERMINAL (PTY) session REST lifecycle against a running
sandbox server.

The ``claude`` command invokes the Claude Code CLI inside the sandbox and
needs ``ANTHROPIC_API_KEY``; when no key is visible on the host running
this script the LLM case is reported as ``[SKIP]`` (see ``E2E_RUN_LLM``
to override).

Usage::

    python3 e2e_test.py                                # http://localhost:9000
    E2E_BASE_URL=http://host:9000 python3 e2e_test.py
    ANTHROPIC_API_KEY=sk-ant-xxx python3 e2e_test.py   # enables the LLM case

Environment variables:

    E2E_BASE_URL     Server base URL                     (default http://localhost:9000)
    ABX_SERVER_TOKEN        Application Bearer token          (default: none — local mode)
    E2E_BASE_DIR     File-ops root inside the container   (default /home/user/app)
    E2E_TIMEOUT      HTTP read timeout in seconds         (default 60)
    E2E_LLM_TIMEOUT  Timeout for the LLM command call     (default 420)
    E2E_RUN_LLM      1 = force the LLM case, 0 = skip it  (default: auto-detect key)
    E2E_MODEL        Override the ``model`` argument      (default: command default)

Notes:

- ``/health`` (CORE) and ``/commands`` (COMMANDS) are always registered;
  FILE_OPS, PROCESS and TERMINAL depend on the server capability configuration.
- File paths are constrained by the server to ``ABX_SERVER_BASE_DIR``
  (default ``/home/user``); keep ``E2E_BASE_DIR`` inside that root.
- The host-side key check is a proxy: the key must also be visible
  *inside* the sandbox for the LLM case to actually succeed.
- The ``claude`` command's CLI contract (see ``commands.py``):
  ``claude -p <prompt> --model <model> --output-format json`` plus explicit tools.
- PTY sessions are exercised through the TERMINAL REST routes only
  (``/pty/sessions``); the interactive WebSocket on port 9001 is not
  touched.

Only ``httpx`` is required — no SDK dependency.
"""
from __future__ import annotations

import base64
import json
import os
import sys
import time
import uuid
from typing import Any

import httpx

# The host runner passes provider gateway authentication separately from app auth.
import json as _e2e_json
_GATEWAY_HEADERS = _e2e_json.loads(os.environ.get("E2E_GATEWAY_HEADERS_JSON", "{}"))
if not isinstance(_GATEWAY_HEADERS, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in _GATEWAY_HEADERS.items()):
    raise ValueError("E2E_GATEWAY_HEADERS_JSON must be an object of string headers")
_APPLICATION_HEADERS = {"Authorization": "Bearer " + os.environ["ABX_SERVER_TOKEN"]} if os.environ.get("ABX_SERVER_TOKEN") else {}

TEMPLATE = "claude-code"
BASE_URL = os.environ.get("E2E_BASE_URL", "http://localhost:9000").rstrip("/")
BASE_DIR = os.environ.get("E2E_BASE_DIR", "/home/user/app").rstrip("/") or "/home/user/app"
TIMEOUT = httpx.Timeout(
    connect=10.0,
    read=float(os.environ.get("E2E_TIMEOUT", "60")),
    write=30.0,
    pool=10.0,
)
LLM_TIMEOUT = float(os.environ.get("E2E_LLM_TIMEOUT", "420"))
MODEL = os.environ.get("E2E_MODEL", "")
RUN_LLM = os.environ.get("E2E_RUN_LLM", "").strip().lower()
REQUIRE = os.environ.get("E2E_REQUIRE_LLM", "").strip().lower() in {"1", "true", "yes"}
MARKER = "ABX_E2E_OK"

# ── Template contract (see commands.py / template.yaml) ────────────────
CMD = "claude"
CMD_ARGS = {
    "prompt": "string", "model": "string", "cwd": "string",
    "allowed_tools": "string", "resume": "string", "command_timeout": "integer",
}  # name -> expected type
REQUIRED_ARGS = ("prompt",)  # required args of CMD (validated by the server)
KEY_ENVS = ("ANTHROPIC_API_KEY",)  # host env vars that enable the LLM case

PROBE_DIR = f"{BASE_DIR}/abx_e2e_{TEMPLATE}_{uuid.uuid4().hex}"
PROBE_FILE = f"{PROBE_DIR}/probe.txt"

RESULTS: list[tuple[str, str, str]] = []  # (status, test, detail)
STATE: dict[str, Any] = {}
OWNED_PTY_SESSIONS: set[str] = set()
OWNED_PROCESS_IDS: set[int] = set()


def record(status: str, test: str, detail: str = "") -> None:
    """Print and remember the result of one check."""
    RESULTS.append((status, test, detail))
    line = f"[{status}] {test}"
    if detail:
        line += f" — {detail}"
    print(line, flush=True)


def _short(value: object, limit: int = 160) -> str:
    """Compact string form of *value* for log lines."""
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _client() -> httpx.Client:
    """Build an httpx client bound to the server base URL."""
    headers = dict(_APPLICATION_HEADERS)
    return httpx.Client(base_url=BASE_URL, timeout=TIMEOUT, headers={**(headers), **_GATEWAY_HEADERS, **_APPLICATION_HEADERS})


def _group_on(name: str) -> bool:
    """Return whether capability group *name* is enabled (default: assume yes)."""
    groups = STATE.get("groups")
    if not isinstance(groups, dict):
        return True  # probe unavailable — attempt anyway, failures stay visible
    return bool(groups.get(name, True))


def _read_sse(response: httpx.Response, max_seconds: float) -> list[dict[str, Any]]:
    """Parse a ``text/event-stream`` response into ``{event, data}`` records."""
    events: list[dict[str, Any]] = []
    event_name = ""
    data_buf: list[str] = []
    deadline = time.monotonic() + max_seconds
    try:
        for line in response.iter_lines():
            if time.monotonic() > deadline:
                events.append({"event": "_timeout", "data": {}})
                break
            if line == "":
                if data_buf:
                    raw = "\n".join(data_buf)
                    try:
                        payload: Any = json.loads(raw)
                    except json.JSONDecodeError:
                        payload = {"_raw": raw}
                    events.append({"event": event_name, "data": payload})
                event_name, data_buf = "", []
                continue
            if line.startswith("event:"):
                event_name = line[len("event:"):].strip()
            elif line.startswith("data:"):
                data_buf.append(line[len("data:"):].strip())
    except httpx.HTTPError as exc:
        events.append({"event": "_error", "data": {"message": str(exc)}})
    return events


def preflight(client: httpx.Client) -> bool:
    """Verify the server is reachable and healthy."""
    try:
        resp = client.get("/health")
        ok = resp.status_code == 200 and resp.json().get("status") == "ok"
        print(f"[{'PASS' if ok else 'FAIL'}] preflight GET /health — HTTP {resp.status_code}",
              flush=True)
        return ok
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] preflight GET /health — {exc}", flush=True)
        return False


# ──────────────────────────────────────────────────────────────────────
# Group 1 — Built-in routes
# ──────────────────────────────────────────────────────────────────────


def group_builtin(client: httpx.Client) -> None:
    # Capability probe — also feeds the FILE_OPS / PROCESS / TERMINAL gates below.
    try:
        resp = client.get("/capabilities")
        body = resp.json()
        groups = body.get("groups", {})
        if resp.status_code == 200 and isinstance(groups, dict):
            STATE["groups"] = groups
            enabled = [g for g, on in sorted(groups.items()) if on]
            record("PASS", "GET /capabilities",
                   f"HTTP {resp.status_code}, enabled: {', '.join(enabled)}")
        elif resp.status_code == 401:
            record("SKIP", "GET /capabilities",
                   "HTTP 401 (auth configured) — pass ABX_SERVER_TOKEN to probe groups")
        else:
            record("FAIL", "GET /capabilities",
                   f"HTTP {resp.status_code}, {_short(body, 120)}")
    except Exception as exc:  # noqa: BLE001
        record("FAIL", "GET /capabilities", f"exception: {exc}")

    # GET /commands — the registered command and its declared args.
    try:
        resp = client.get("/commands")
        body = resp.json()
        entries = body.get("commands", body if isinstance(body, list) else [])
        by_name = {c.get("name"): c for c in entries if isinstance(c, dict)}
        entry = by_name.get(CMD) or {}
        args = {a.get("name"): a.get("type") for a in entry.get("args", [])
                if isinstance(a, dict)}
        missing = [n for n in CMD_ARGS if n not in args]
        typed = [f"{n}:{args.get(n)}" for n, t in CMD_ARGS.items() if n in args and args[n] != t]
        ok = resp.status_code == 200 and entry != {} and not missing and not typed
        record("PASS" if ok else "FAIL", "GET /commands",
               f"HTTP {resp.status_code}, {len(by_name)} command(s), "
               f"{CMD} args={sorted(f'{n}:{t}' for n, t in args.items())}"
               + (f", missing={missing}" if missing else "")
               + (f", unexpected types={typed}" if typed else ""))
    except Exception as exc:  # noqa: BLE001
        record("FAIL", "GET /commands", f"exception: {exc}")

    # Unknown command must be rejected with 404.
    try:
        resp = client.post("/commands/__no_such_command__", json={})
        body = resp.json()
        ok = resp.status_code == 404 and body.get("type") == "ValueError"
        record("PASS" if ok else "FAIL", "POST /commands (unknown name)",
               f"HTTP {resp.status_code} (expected 404), type={body.get('type')}")
    except Exception as exc:  # noqa: BLE001
        record("FAIL", "POST /commands (unknown name)", f"exception: {exc}")

    # Missing required argument must be rejected with 400.
    if REQUIRED_ARGS:
        try:
            resp = client.post(f"/commands/{CMD}", json={})
            body = resp.json()
            ok = resp.status_code == 400 and "Required argument" in str(body.get("error", ""))
            record("PASS" if ok else "FAIL", f"POST /commands/{CMD} (no args)",
                   f"HTTP {resp.status_code} (expected 400), error={_short(body.get('error'), 100)}")
        except Exception as exc:  # noqa: BLE001
            record("FAIL", f"POST /commands/{CMD} (no args)", f"exception: {exc}")
    else:
        record("SKIP", f"POST /commands/{CMD} (no args)",
               "command has no required args — validation case not applicable")


# ──────────────────────────────────────────────────────────────────────
# Group 2 — File ops (FILE_OPS)
# ──────────────────────────────────────────────────────────────────────


def group_files(client: httpx.Client) -> None:
    if not _group_on("file_ops"):
        for test in ("POST /files/upload-stream", "GET /files/stat", "GET /files/list",
                     "POST /files/search", "GET /files/download-stream", "DELETE /files"):
            record("SKIP", test, "FILE_OPS capability group is disabled")
        return

    payload = f"{TEMPLATE} e2e probe {os.getpid()}\n".encode()
    encoded = base64.b64encode(payload).decode()

    # 1. Upload
    seeded = False
    try:
        resp = client.post("/files/upload-stream",
                           json={"path": PROBE_FILE, "content_base64": encoded})
        body = resp.json()
        seeded = (resp.status_code == 200 and body.get("bytes") == len(payload)
                  and str(body.get("path", "")).endswith("probe.txt"))
        record("PASS" if seeded else "FAIL", "POST /files/upload-stream",
               f"HTTP {resp.status_code}, bytes={body.get('bytes')}, path={body.get('path')}")
    except Exception as exc:  # noqa: BLE001
        record("FAIL", "POST /files/upload-stream", f"exception: {exc}")

    if not seeded:
        for test in ("GET /files/stat", "GET /files/list", "POST /files/search",
                     "GET /files/download-stream", "DELETE /files"):
            record("SKIP", test, "probe file was not uploaded")
        return

    # 2. Stat
    try:
        resp = client.get("/files/stat", params={"path": PROBE_FILE})
        body = resp.json()
        ok = (resp.status_code == 200 and body.get("exists") is True
              and body.get("type") == "file" and body.get("size") == len(payload))
        record("PASS" if ok else "FAIL", "GET /files/stat",
               f"HTTP {resp.status_code}, exists={body.get('exists')}, "
               f"type={body.get('type')}, size={body.get('size')}")
    except Exception as exc:  # noqa: BLE001
        record("FAIL", "GET /files/stat", f"exception: {exc}")

    # 3. List
    try:
        resp = client.get("/files/list", params={"path": PROBE_DIR})
        body = resp.json()
        entries = body.get("entries", [])
        names = [e.get("name") for e in entries if isinstance(e, dict)]
        ok = resp.status_code == 200 and "probe.txt" in names
        record("PASS" if ok else "FAIL", "GET /files/list",
               f"HTTP {resp.status_code}, {len(names)} entr(ies), probe.txt present={'probe.txt' in names}")
    except Exception as exc:  # noqa: BLE001
        record("FAIL", "GET /files/list", f"exception: {exc}")

    # 4. Search
    try:
        resp = client.post("/files/search", json={"path": PROBE_DIR, "pattern": "*.txt"})
        body = resp.json()
        results = body.get("results", [])
        names = [r.get("name") for r in results if isinstance(r, dict)]
        ok = resp.status_code == 200 and "probe.txt" in names
        record("PASS" if ok else "FAIL", "POST /files/search",
               f"HTTP {resp.status_code}, {len(names)} match(es)")
    except Exception as exc:  # noqa: BLE001
        record("FAIL", "POST /files/search", f"exception: {exc}")

    # 5. Download round-trip
    try:
        resp = client.get("/files/download-stream", params={"path": PROBE_FILE})
        body = resp.json()
        decoded = base64.b64decode(body.get("content_base64", ""))
        ok = resp.status_code == 200 and decoded == payload
        record("PASS" if ok else "FAIL", "GET /files/download-stream",
               f"HTTP {resp.status_code}, content matches={decoded == payload}")
    except Exception as exc:  # noqa: BLE001
        record("FAIL", "GET /files/download-stream", f"exception: {exc}")

    # 6. Delete + verify gone
    try:
        resp = client.delete("/files", params={"path": PROBE_FILE})
        body = resp.json()
        follow = client.get("/files/stat", params={"path": PROBE_FILE}).json()
        ok = (resp.status_code == 200 and body.get("deleted") is True
              and follow.get("exists") is False)
        record("PASS" if ok else "FAIL", "DELETE /files",
               f"HTTP {resp.status_code}, deleted={body.get('deleted')}, "
               f"re-stat exists={follow.get('exists')}")
    except Exception as exc:  # noqa: BLE001
        record("FAIL", "DELETE /files", f"exception: {exc}")


# ──────────────────────────────────────────────────────────────────────
# Group 3 — Shell & process (PROCESS)
# ──────────────────────────────────────────────────────────────────────


def group_shell_process(client: httpx.Client) -> None:
    if not _group_on("process"):
        for test in ("POST /shell", "POST /shell/stream", "POST /process/start",
                     "GET /process/list", "GET /process/{pid}", "POST /process/{pid}/signal"):
            record("SKIP", test, "PROCESS capability group is disabled")
        return

    marker = f"abx-e2e-{TEMPLATE}"

    # 1. Plain shell execution
    try:
        resp = client.post("/shell", json={"command": f"echo {marker}"})
        body = resp.json()
        ok = (resp.status_code == 200 and body.get("exit_code") == 0
              and marker in str(body.get("stdout", "")))
        record("PASS" if ok else "FAIL", "POST /shell",
               f"HTTP {resp.status_code}, exit={body.get('exit_code')}, "
               f"stdout={str(body.get('stdout', '')).strip()!r}")
    except Exception as exc:  # noqa: BLE001
        record("FAIL", "POST /shell", f"exception: {exc}")

    # 2. Streaming shell (SSE)
    try:
        status = 0
        events: list[dict[str, Any]] = []
        with client.stream("POST", "/shell/stream",
                           json={"command": f"echo {marker}", "timeout": 30}) as resp:
            status = resp.status_code
            if status == 200:
                events = _read_sse(resp, 30.0)
            else:
                events = []
                raw = resp.read().decode("utf-8", "replace")
        stdout_text = "\n".join(str((e.get("data") or {}).get("data", ""))
                                for e in events if e.get("event") == "stdout")
        exits = [(e.get("data") or {}).get("exit_code")
                 for e in events if e.get("event") == "exit"]
        ok = status == 200 and marker in stdout_text and bool(exits) and exits[-1] == 0
        detail = f"HTTP {status}, {len(events)} events, exit={exits[-1] if exits else None}"
        if status != 200:
            detail += f", body={_short(raw, 120)}"
        record("PASS" if ok else "FAIL", "POST /shell/stream", detail)
    except Exception as exc:  # noqa: BLE001
        record("FAIL", "POST /shell/stream", f"exception: {exc}")

    # 3. Background process lifecycle
    pid: int | None = None
    try:
        resp = client.post("/process/start", json={"command": "sleep 60"})
        body = resp.json()
        pid = body.get("pid") if isinstance(body.get("pid"), int) else None
        if pid is not None:
            OWNED_PROCESS_IDS.add(pid)
        ok = resp.status_code == 200 and pid is not None
        record("PASS" if ok else "FAIL", "POST /process/start",
               f"HTTP {resp.status_code}, pid={pid}")
    except Exception as exc:  # noqa: BLE001
        record("FAIL", "POST /process/start", f"exception: {exc}")

    if pid is None:
        for test in ("GET /process/list", "GET /process/{pid}", "POST /process/{pid}/signal"):
            record("SKIP", test, "no background process was started")
        return

    # 4. List contains the new pid
    try:
        resp = client.get("/process/list")
        body = resp.json()
        pids = [p.get("pid") for p in body.get("processes", []) if isinstance(p, dict)]
        ok = resp.status_code == 200 and pid in pids
        record("PASS" if ok else "FAIL", "GET /process/list",
               f"HTTP {resp.status_code}, {len(pids)} process(es), pid present={pid in pids}")
    except Exception as exc:  # noqa: BLE001
        record("FAIL", "GET /process/list", f"exception: {exc}")

    # 5. Detail reports "running"
    try:
        resp = client.get(f"/process/{pid}")
        body = resp.json()
        ok = resp.status_code == 200 and body.get("state") == "running"
        record("PASS" if ok else "FAIL", "GET /process/{pid}",
               f"HTTP {resp.status_code}, state={body.get('state')}")
    except Exception as exc:  # noqa: BLE001
        record("FAIL", "GET /process/{pid}", f"exception: {exc}")

    # 6. Signal (SIGTERM) then wait for exit
    try:
        resp = client.post(f"/process/{pid}/signal", json={"signal": 15})
        ok = resp.status_code == 200
        state, code = "", None
        if ok:
            deadline = time.monotonic() + 6.0
            while time.monotonic() < deadline:
                detail_body = client.get(f"/process/{pid}").json()
                state, code = detail_body.get("state"), detail_body.get("exit_code")
                if state == "exited":
                    break
                time.sleep(0.3)
        ok = ok and state == "exited"
        record("PASS" if ok else "FAIL", "POST /process/{pid}/signal",
               f"HTTP {resp.status_code}, final state={state}, exit_code={code}")
    except Exception as exc:  # noqa: BLE001
        record("FAIL", "POST /process/{pid}/signal", f"exception: {exc}")


# ──────────────────────────────────────────────────────────────────────
# Group 4 — Template command (Claude Code CLI, LLM-gated)
# ──────────────────────────────────────────────────────────────────────


def group_command(client: httpx.Client) -> None:
    test = f"POST /commands/{CMD}"

    forced_off = RUN_LLM in {"0", "false", "no"}
    has_key = any(os.environ.get(k, "").strip() for k in KEY_ENVS)
    if REQUIRE and forced_off:
        record("FAIL", test, "E2E_REQUIRE_LLM=1 conflicts with E2E_RUN_LLM=0")
        return
    if forced_off:
        record("SKIP", test, f"E2E_RUN_LLM={RUN_LLM!r} — forced skip")
        return
    if not has_key:
        status = "FAIL" if REQUIRE or RUN_LLM in {"1", "true", "yes"} else "SKIP"
        record(status, test, f"missing {'/'.join(KEY_ENVS)}")
        return

    # Seed a broken project; require tool use and verify files independently.
    project = f"{PROBE_DIR}/agent-project"
    source = "def add(a, b):\n    return a - b\n"
    test_source = (
        "import unittest\nfrom calculator import add\n"
        "class TestAdd(unittest.TestCase):\n"
        "    def test_positive(self): self.assertEqual(add(2, 3), 5)\n"
        "    def test_negative(self): self.assertEqual(add(-2, -3), -5)\n"
        "if __name__ == '__main__': unittest.main()\n"
    )
    try:
        for name, content in (("calculator.py", source), ("test_calculator.py", test_source)):
            resp = client.post("/files/upload-stream", json={
                "path": f"{project}/{name}",
                "content_base64": base64.b64encode(content.encode()).decode(),
            })
            resp.raise_for_status()
        # Before invoking the agent, the test must fail for the intended bug.
        command = "python3 -m unittest -v"
        before = client.post("/shell", json={"command": command, "cwd": project}).json()
        if before.get("exit_code") != 1 or "AssertionError" not in before.get("stderr", ""):
            record("FAIL", test, "seeded project did not reproduce the expected failing test")
            return
        payload: dict[str, Any] = {
            "prompt": (
                "Fix calculator.py so add(a,b) returns the sum. Do not modify "
                "test_calculator.py. Run python3 -m unittest -v and make all tests pass. "
                "Create agent-created.txt containing exactly ABX_E2E_OK followed by a newline, "
                "and report.txt describing the fix and test result. End your response with ABX_E2E_OK."
            ),
            "cwd": project,
            "allowed_tools": "Read,Edit,Write,Bash(python3:*)",
        }
        if MODEL:
            payload["model"] = MODEL
        resp = client.post(f"/commands/{CMD}", json=payload, timeout=LLM_TIMEOUT)
        body = resp.json()
        result = body.get("result")
        found = isinstance(result, str) and MARKER in result
        if resp.status_code != 200 or not found:
            record("FAIL", test, f"HTTP {resp.status_code}, response marker={found}")
            return

        def read_file(name: str) -> str:
            response = client.get("/files/download-stream", params={"path": f"{project}/{name}"})
            response.raise_for_status()
            return base64.b64decode(response.json()["content_base64"]).decode()

        modified = read_file("calculator.py")
        original_test = read_file("test_calculator.py")
        artifact = read_file("agent-created.txt")
        report = read_file("report.txt")
        after_response = client.post("/shell", json={"command": command, "cwd": project})
        after = after_response.json()
        ok = (
            modified != source and original_test == test_source
            and artifact == MARKER + "\n" and bool(report.strip())
            and after_response.status_code == 200 and after.get("exit_code") == 0
            and "Ran 2 tests" in after.get("stderr", "")
        )
        record("PASS" if ok else "FAIL", test,
               f"real agent: source changed={modified != source}, tests preserved={original_test == test_source}, "
               f"artifact valid={artifact == MARKER + chr(10)}, test exit={after.get('exit_code')}")
    except Exception as exc:  # noqa: BLE001
        record("FAIL", test, f"agent acceptance exception: {type(exc).__name__}")


# ──────────────────────────────────────────────────────────────────────
# Group 5 — PTY sessions (TERMINAL, REST only)
# ──────────────────────────────────────────────────────────────────────


def group_pty(client: httpx.Client) -> None:
    if not _group_on("terminal"):
        for test in ("POST /pty/sessions", "GET /pty/sessions", "DELETE /pty/sessions/{id}"):
            record("SKIP", test, "TERMINAL capability group is disabled")
        return

    session_id = ""
    try:
        resp = client.post("/pty/sessions", json={"cols": 80, "rows": 24})
        body = resp.json()
        session_id = str(body.get("session_id", ""))
        if session_id:
            OWNED_PTY_SESSIONS.add(session_id)
        ok = (resp.status_code == 200 and bool(session_id)
              and str(body.get("ws_url", "")).startswith(("ws://", "wss://"))
              and isinstance(body.get("pid"), int))
        record("PASS" if ok else "FAIL", "POST /pty/sessions",
               f"HTTP {resp.status_code}, session={session_id}, ws_url={body.get('ws_url')}")
    except Exception as exc:  # noqa: BLE001
        record("FAIL", "POST /pty/sessions", f"exception: {exc}")

    if not session_id:
        record("SKIP", "GET /pty/sessions", "no PTY session was created")
        record("SKIP", "DELETE /pty/sessions/{id}", "no PTY session was created")
        return

    try:
        resp = client.get("/pty/sessions")
        body = resp.json()
        ids = [s.get("id") for s in body.get("sessions", []) if isinstance(s, dict)]
        ok = resp.status_code == 200 and session_id in ids
        record("PASS" if ok else "FAIL", "GET /pty/sessions",
               f"HTTP {resp.status_code}, {len(ids)} session(s), present={session_id in ids}")
    except Exception as exc:  # noqa: BLE001
        record("FAIL", "GET /pty/sessions", f"exception: {exc}")

    try:
        resp = client.delete(f"/pty/sessions/{session_id}")
        body = resp.json()
        follow = client.delete(f"/pty/sessions/{session_id}")
        ok = (resp.status_code == 200 and body.get("status") == "closed"
              and follow.status_code == 404)
        if resp.status_code == 200:
            OWNED_PTY_SESSIONS.discard(session_id)
        record("PASS" if ok else "FAIL", "DELETE /pty/sessions/{id}",
               f"HTTP {resp.status_code}, status={body.get('status')}, "
               f"re-DELETE={follow.status_code}")
    except Exception as exc:  # noqa: BLE001
        record("FAIL", "DELETE /pty/sessions/{id}", f"exception: {exc}")


# ──────────────────────────────────────────────────────────────────────
# Cleanup & summary
# ──────────────────────────────────────────────────────────────────────


def cleanup(client: httpx.Client) -> None:
    """Remove only resources created by this invocation, including failed cases."""
    for sid in list(OWNED_PTY_SESSIONS):
        try:
            resp = client.delete(f"/pty/sessions/{sid}")
            if resp.status_code in {200, 404}:
                OWNED_PTY_SESSIONS.discard(sid)
        except Exception:
            print("[cleanup] owned PTY session cleanup failed", flush=True)
    for pid in list(OWNED_PROCESS_IDS):
        try:
            client.post(f"/process/{pid}/signal", json={"signal": 15})
        except Exception:
            print("[cleanup] owned process cleanup failed", flush=True)
    try:
        resp = client.delete("/files", params={"path": PROBE_DIR})
        print(f"[cleanup] owned probe directory -> HTTP {resp.status_code}", flush=True)
    except Exception:
        print("[cleanup] owned probe directory cleanup failed", flush=True)


def summary() -> int:
    """Print the aggregate report and return the process exit code."""
    passed = sum(1 for s, _, _ in RESULTS if s == "PASS")
    failed = sum(1 for s, _, _ in RESULTS if s == "FAIL")
    skipped = sum(1 for s, _, _ in RESULTS if s == "SKIP")
    print("\n" + "=" * 74, flush=True)
    print(f"SUMMARY — {TEMPLATE}", flush=True)
    print("=" * 74, flush=True)
    print(f"{passed} passed, {failed} failed, {skipped} skipped (total {len(RESULTS)})",
          flush=True)
    if failed:
        print("\nFailed tests:", flush=True)
        for s, t, d in RESULTS:
            if s == "FAIL":
                print(f"  - {t}: {d}", flush=True)
    print("=" * 74, flush=True)
    return 1 if failed else 0


def legacy_main() -> int:
    print(f"{TEMPLATE} end-to-end suite", flush=True)
    print(f"  base_url : {BASE_URL}", flush=True)
    print(f"  base_dir : {BASE_DIR}", flush=True)
    print(f"  llm case : " + ("forced" if RUN_LLM in {"1", "true", "yes"} else "auto"),
          flush=True)
    print("-" * 74, flush=True)
    with _client() as client:
        if not preflight(client):
            print("server unreachable — aborting", flush=True)
            return 2
        try:
            print("\n-- Built-in routes --", flush=True)
            group_builtin(client)
            print("\n-- File ops (FILE_OPS) --", flush=True)
            group_files(client)
            print("\n-- Shell & process (PROCESS) --", flush=True)
            group_shell_process(client)
            print("\n-- Template command --", flush=True)
            group_command(client)
            print("\n-- PTY sessions (TERMINAL) --", flush=True)
            group_pty(client)
        finally:
            cleanup(client)
    return summary()


def main() -> int:
    # Keep existing Anthropic controller helpers and their ownership regressions.
    # Current qualification uses the separate strict original-native BYOK controller.
    import importlib.util
    from pathlib import Path
    spec=importlib.util.spec_from_file_location('claude_strict_byok_controller',Path(__file__).with_name('byok_e2e_test.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    try:return module.main()
    except Exception as exc:
        print('[FAIL] original Claude controller aborted ('+type(exc).__name__+'); diagnostics='+json.dumps(module.safe_diagnostic(str(exc)),sort_keys=True)+'; private output omitted',flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
