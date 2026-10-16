#!/usr/bin/env python3
"""End-to-end test suite for the ``python-hello`` template.

Exercises built-in routes (/health, /commands), custom commands (hello,
run_script, _debug_info), the custom GET /hello/{name} route, FILE_OPS
file round-trip and PROCESS shell execution against a running server.

Usage::

    python3 e2e_test.py                                # http://localhost:9000
    E2E_BASE_URL=http://host:9000 python3 e2e_test.py
"""
from __future__ import annotations

import base64
import json
import os
import sys
import uuid

import httpx

BASE_URL = os.environ.get("E2E_BASE_URL", "http://localhost:9000").rstrip("/")
WORKSPACE = os.environ.get("E2E_WORKSPACE", "")  # empty → auto-detect
TIMEOUT = httpx.Timeout(connect=10.0, read=60.0, write=30.0, pool=10.0)
TOKEN = os.environ.get("E2E_TOKEN", "")

RESULTS: list[tuple[str, str, str]] = []  # (status, test, detail)


def record(status: str, test: str, detail: str = "") -> None:
    RESULTS.append((status, test, detail))
    line = f"[{status}] {test}"
    if detail:
        line += f" — {detail}"
    print(line, flush=True)


def _short(value: object, limit: int = 160) -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return text if len(text) <= limit else text[: limit - 3] + "..."


def run_cmd(client: httpx.Client, name: str, kwargs: dict | None = None):
    """POST /commands/{name}, return (status_code, body)."""
    return client.post(f"/commands/{name}", json=kwargs or {})


def cmd_ok(client: httpx.Client, test: str, name: str, kwargs: dict | None,
           check) -> None:
    """Run a custom command and assert via *check(result)*."""
    try:
        resp = run_cmd(client, name, kwargs)
        body = resp.json()
        ok = resp.status_code == 200 and "result" in body and check(body["result"])
        record("PASS" if ok else "FAIL", test,
               f"HTTP {resp.status_code}, {_short(body, 150)}")
    except Exception as exc:  # noqa: BLE001
        record("FAIL", test, f"exception: {exc}")


def preflight(client: httpx.Client) -> bool:
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
    try:
        resp = client.get("/commands")
        body = resp.json()
        names = {c.get("name") for c in body.get("commands", body if isinstance(body, list) else [])}
        ok = (
            resp.status_code == 200
            and "hello" in names
            and {"run_script", "run", "test"} <= names
            and "_debug_info" not in names  # hidden commands are not listed
        )
        record("PASS" if ok else "FAIL", "GET /commands",
               f"HTTP {resp.status_code}, listed={sorted(n for n in names if n)}")
    except Exception as exc:  # noqa: BLE001
        record("FAIL", "GET /commands", f"exception: {exc}")


# ──────────────────────────────────────────────────────────────────────
# Group 2 — Custom commands
# ──────────────────────────────────────────────────────────────────────


def group_commands(client: httpx.Client) -> None:
    cmd_ok(client, "POST /commands/hello", "hello", {"name": "E2E"},
           lambda r: r == "Hello, E2E!")

    cmd_ok(client, "POST /commands/hello (default)", "hello", {},
           lambda r: r == "Hello, World!")

    cmd_ok(client, "POST /commands/run_script", "run_script",
           {"code": "print(21 * 2)"},
           lambda r: r.strip() == "42")

    try:
        marker = "synthetic-private-python-value"
        resp = run_cmd(client, "run_script", {
            "code": f"import sys; print('{marker}', file=sys.stderr); sys.exit(3)"
        })
        ok = (resp.status_code == 500 and "error" in resp.json()
              and marker not in resp.text and "exited 3" in resp.json()["error"])
        record("PASS" if ok else "FAIL", "POST /commands/run_script (error)",
               f"HTTP {resp.status_code} (expected 500)")
    except Exception as exc:  # noqa: BLE001
        record("FAIL", "POST /commands/run_script (error)", f"exception: {exc}")

    for name, arguments, expected in (
        ("run_script", {}, 400),
        ("unknown_e2e_command", {}, 404),
    ):
        resp = run_cmd(client, name, arguments)
        record("PASS" if resp.status_code == expected else "FAIL",
               f"{name} argument/routing error", f"HTTP {resp.status_code} (expected {expected})")

    # Hidden command is callable even though not listed.
    cmd_ok(client, "POST /commands/_debug_info (hidden)", "_debug_info", {},
           lambda r: isinstance(r, dict) and "python" in r and "system" in r)


# ──────────────────────────────────────────────────────────────────────
# Group 3 — Custom HTTP route
# ──────────────────────────────────────────────────────────────────────


def group_routes(client: httpx.Client) -> None:
    try:
        resp = client.get("/hello/E2E")
        body = resp.json()
        ok = resp.status_code == 200 and body.get("greeting") == "Hello, E2E!"
        record("PASS" if ok else "FAIL", "GET /hello/{name}",
               f"HTTP {resp.status_code}, greeting={body.get('greeting')!r}")
    except Exception as exc:  # noqa: BLE001
        record("FAIL", "GET /hello/{name}", f"exception: {exc}")


# ──────────────────────────────────────────────────────────────────────
# Group 4 — File ops (FILE_OPS)
# ──────────────────────────────────────────────────────────────────────


def detect_workspace(client: httpx.Client) -> str:
    """Use the explicit workspace or ask the command process for its real cwd.

    A rejected file operation is a failure, never a reason to try another path.
    """
    if WORKSPACE:
        return WORKSPACE
    resp = run_cmd(client, "run_script", {"code": "import os; print(os.getcwd())"})
    resp.raise_for_status()
    workspace = str(resp.json()["result"]).strip()
    if not workspace.startswith("/"):
        raise RuntimeError("run_script did not return an absolute workspace")
    return workspace


def group_files(client: httpx.Client) -> None:
    if not WORKSPACE:
        record("FAIL", "files upload/download round-trip",
               "workspace discovery failed — set E2E_WORKSPACE")
        return
    filename = f"e2e_python_hello_{uuid.uuid4().hex}.txt"
    path = f"{WORKSPACE}/{filename}"
    content = "python-hello e2e file round-trip\n"
    encoded = base64.b64encode(content.encode()).decode()

    try:
        resp = client.post("/files/upload-stream",
                           json={"path": path, "content_base64": encoded})
        ok = resp.status_code == 200
        record("PASS" if ok else "FAIL", "POST /files/upload-stream",
               f"HTTP {resp.status_code}, {_short(resp.json(), 120)}")
        if not ok:
            return
    except Exception as exc:  # noqa: BLE001
        record("FAIL", "POST /files/upload-stream", f"exception: {exc}")
        return

    try:
        resp = client.get("/files/download-stream", params={"path": path})
        body = resp.json()
        ok = resp.status_code == 200 and body.get("content_base64") == encoded
        record("PASS" if ok else "FAIL", "GET /files/download-stream",
               f"HTTP {resp.status_code}, content matches={ok}")
    except Exception as exc:  # noqa: BLE001
        record("FAIL", "GET /files/download-stream", f"exception: {exc}")

    try:
        resp = client.get("/files/list", params={"path": WORKSPACE})
        entries = resp.json().get("entries", resp.json().get("files", []))
        names = [e.get("name") for e in entries] if isinstance(entries, list) else []
        ok = resp.status_code == 200 and filename in names
        record("PASS" if ok else "FAIL", "GET /files/list",
               f"HTTP {resp.status_code}, {len(names)} entr(ies), file present={ok}")
    except Exception as exc:  # noqa: BLE001
        record("FAIL", "GET /files/list", f"exception: {exc}")

    try:
        resp = client.delete("/files", params={"path": path})
        ok = resp.status_code == 200
        record("PASS" if ok else "FAIL", "DELETE /files",
               f"HTTP {resp.status_code}")
    except Exception as exc:  # noqa: BLE001
        record("FAIL", "DELETE /files", f"exception: {exc}")


def group_python_workflow(client: httpx.Client) -> None:
    """Upload real source/tests, execute them, and prove a failing test fails."""
    if not WORKSPACE:
        record("FAIL", "Python development workflow", "workspace unavailable")
        return
    marker = uuid.uuid4().hex
    source = f"e2e_python_{marker}.py"
    test_file = f"e2e_pytest_{marker}.py"
    failing_test_file = f"e2e_pytest_failing_{marker}.py"
    files = {
        source: "print(6 * 7)\n",
        test_file: "def test_calculation():\n    assert 6 * 7 == 42\n",
    }
    uploaded = []
    try:
        for name, content in files.items():
            path = f"{WORKSPACE}/{name}"
            resp = client.post("/files/upload-stream", json={
                "path": path,
                "content_base64": base64.b64encode(content.encode()).decode(),
            })
            if resp.status_code != 200:
                record("FAIL", "upload Python workflow", f"HTTP {resp.status_code}")
                return
            uploaded.append(path)
        cmd_ok(client, "run uploaded script", "run", {"file": source},
               lambda result: result.strip() == "42")
        cmd_ok(client, "pytest uploaded test", "test", {"path": test_file},
               lambda result: "1 passed" in result)
        # A same-size rewrite within one timestamp tick can reuse pytest's
        # assertion-rewrite bytecode cache. Use a fresh negative-control module
        # so the check always executes the failing source, including on fast CI.
        failing_path = f"{WORKSPACE}/{failing_test_file}"
        resp = client.post("/files/upload-stream", json={
            "path": failing_path,
            "content_base64": base64.b64encode(
                b"def test_calculation():\n    assert 6 * 7 == 41\n"
            ).decode(),
        })
        if resp.status_code != 200:
            record("FAIL", "upload failing Python test", f"HTTP {resp.status_code}")
            return
        uploaded.append(failing_path)
        resp = run_cmd(client, "test", {"path": failing_test_file})
        ok = resp.status_code == 500 and "error" in resp.json()
        record("PASS" if ok else "FAIL", "pytest failing test returns sanitized 500",
               f"HTTP {resp.status_code}")
    except Exception as exc:
        record("FAIL", "Python development workflow", str(exc))
    finally:
        for path in uploaded:
            resp = client.delete("/files", params={"path": path})
            record("PASS" if resp.status_code == 200 else "FAIL", "cleanup Python workflow",
                   f"HTTP {resp.status_code}")


# ──────────────────────────────────────────────────────────────────────
# Group 5 — Shell (PROCESS)
# ──────────────────────────────────────────────────────────────────────


def group_shell(client: httpx.Client) -> None:
    try:
        resp = client.post("/shell", json={"command": "echo hello"})
        body = resp.json()
        stdout = str(body.get("stdout", ""))
        ok = resp.status_code == 200 and "hello" in stdout
        record("PASS" if ok else "FAIL", "POST /shell echo",
               f"HTTP {resp.status_code}, stdout={stdout.strip()!r}")
    except Exception as exc:  # noqa: BLE001
        record("FAIL", "POST /shell echo", f"exception: {exc}")


def summary() -> int:
    passed = sum(1 for s, _, _ in RESULTS if s == "PASS")
    failed = sum(1 for s, _, _ in RESULTS if s == "FAIL")
    skipped = sum(1 for s, _, _ in RESULTS if s == "SKIP")
    print("\n" + "=" * 74, flush=True)
    print("SUMMARY — python-hello", flush=True)
    print("=" * 74, flush=True)
    print(f"{passed} passed, {failed} failed, {skipped} skipped "
          f"(total {len(RESULTS)})", flush=True)
    if failed:
        print("\nFailed tests:", flush=True)
        for s, t, d in RESULTS:
            if s == "FAIL":
                print(f"  - {t}: {d}", flush=True)
    print("=" * 74, flush=True)
    return 1 if failed else 0


def main() -> int:
    print("python-hello end-to-end suite", flush=True)
    print(f"  base_url : {BASE_URL}", flush=True)
    print("-" * 74, flush=True)
    headers = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}
    with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT, headers=headers) as client:
        if not preflight(client):
            print("server unreachable — aborting", flush=True)
            return 2
        print("\n-- Built-in routes --", flush=True)
        group_builtin(client)
        print("\n-- Custom commands --", flush=True)
        group_commands(client)
        print("\n-- Custom routes --", flush=True)
        group_routes(client)
        print("\n-- File ops --", flush=True)
        global WORKSPACE
        try:
            WORKSPACE = detect_workspace(client)
        except Exception as exc:
            record("FAIL", "workspace discovery", str(exc))
            WORKSPACE = ""
        group_files(client)
        print("\n-- Python development workflow --", flush=True)
        group_python_workflow(client)
        print("\n-- Shell --", flush=True)
        group_shell(client)
    return summary()


if __name__ == "__main__":
    sys.exit(main())
