#!/usr/bin/env python3
"""Real Chromium acceptance over HTTP; missing browser is a failure, never a pass."""
from __future__ import annotations

import base64
from concurrent.futures import ThreadPoolExecutor
import json
import os
import sys
from urllib.parse import quote

import httpx

BASE_URL = os.environ.get("E2E_BASE_URL", "http://localhost:9000").rstrip("/")
WORKSPACE = os.environ.get("E2E_WORKSPACE", "/home/user/app")
HTML = """<html><head><title>ABX_E2E_OK</title></head><body>
<h1>ABX_E2E_OK</h1><a href='https://example.com/'>Example</a>
<input id='email'><input id='password' type='password'>
<script>document.querySelector('#password').addEventListener('input', e => {
 document.title=e.target.value; location.hash=e.target.value;
});</script></body></html>"""
URL = "data:text/html," + quote(HTML)
SYNTHETIC_VALUE = "synthetic-sensitive-value-DO-NOT-ECHO"
FAILED = 0
PASSED = 0


def check(name: str, condition: bool) -> None:
    global FAILED, PASSED
    if condition:
        PASSED += 1
    else:
        FAILED += 1
    # No response dumps: tested pages can carry sensitive form contents.
    print(f"[{'PASS' if condition else 'FAIL'}] {name}", flush=True)


def main() -> int:
    token = os.environ.get("E2E_TOKEN") or os.environ.get("ABX_SERVER_TOKEN", "")
    headers = {"Authorization": "Bearer " + token} if token else {}
    with httpx.Client(base_url=BASE_URL, timeout=180, headers=headers) as client:
        check("server health", client.get("/health").status_code == 200)
        listed = client.get("/commands")
        names = {entry["name"] for entry in listed.json().get("commands", [])}
        check("named commands registered", {"browse", "scrape", "fill_form", "run"} <= names)
        probe = client.post("/commands/browse", json={"url": URL, "action": "extract"})
        check("required real Chromium navigation and body extraction", probe.status_code == 200
              and probe.json().get("result", {}).get("text", "").startswith("ABX_E2E_OK"))
        if probe.status_code != 200:
            print("[FAIL] Chromium is required; install pinned Playwright and its browser. No browser checks are skipped.")
            return 1
        check("page title", probe.json()["result"]["title"] == "ABX_E2E_OK")
        for action, path_key in (("screenshot", "path"), ("full", "screenshot")):
            response = client.post("/commands/browse", json={"url": URL, "action": action})
            check(f"{action} invocation", response.status_code == 200)
            path = response.json().get("result", {}).get(path_key)
            if not path:
                check(f"{action} artifact path", False)
                continue
            try:
                download = client.get("/files/download-stream", params={"path": path})
                data = base64.b64decode(download.json().get("content_base64", ""))
                check(f"{action} remote PNG artifact", download.status_code == 200
                      and data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) > 100)
            finally:
                client.delete("/files", params={"path": path})
        links = client.post("/commands/browse", json={"url": URL, "action": "links"})
        check("real hyperlink extraction", links.status_code == 200 and links.json()["result"]["links"]
              == [{"href": "https://example.com/", "text": "Example"}])
        scrape = client.post("/commands/scrape", json={"url": URL, "selector": "h1"})
        check("CSS extraction", scrape.status_code == 200 and scrape.json()["result"]
              == {"count": 1, "texts": ["ABX_E2E_OK"]})
        empty = client.post("/commands/scrape", json={"url": URL, "selector": ".absent"})
        check("empty CSS match", empty.status_code == 200 and empty.json()["result"]
              == {"count": 0, "texts": []})
        filled = client.post("/commands/fill_form", json={"url": URL, "fields_json": json.dumps([
            {"selector": "#email", "value": "sample@example.invalid"},
            {"selector": "#password", "value": SYNTHETIC_VALUE},
        ])})
        check("real verified form fill without value/DOM/URL echo", filled.status_code == 200
              and filled.json() == {"result": {"fields_filled": 2}}
              and SYNTHETIC_VALUE not in filled.text)
        failed_fill = client.post("/commands/fill_form", json={"url": URL, "timeout_s": 1,
            "fields_json": json.dumps([{"selector": "#missing", "value": SYNTHETIC_VALUE}])})
        check("failed fill has sanitized error", failed_fill.status_code == 500
              and SYNTHETIC_VALUE not in failed_fill.text and "Request values are omitted" in failed_fill.text)
        bad_args = [
            ("browse", {}),
            ("browse", {"url": URL, "timeout_s": "not-an-integer"}),
        ]
        for index, (name, args) in enumerate(bad_args):
            response = client.post(f"/commands/{name}", json=args)
            check(f"argument validation 400 case {index}", response.status_code == 400)
        invalid_execution = [
            ("browse", {"url": URL, "action": "unknown"}),
            ("browse", {"url": "file:///etc/passwd"}),
            ("browse", {"url": URL, "timeout_s": 0}),
            ("fill_form", {"url": URL, "fields_json": "{}"}),
            ("fill_form", {"url": URL, "fields_json": '[{"selector":"#email","value":2}]'}),
        ]
        for index, (name, args) in enumerate(invalid_execution):
            response = client.post(f"/commands/{name}", json=args)
            check(f"execution validation 500 case {index}", response.status_code == 500)
        check("unknown command 404", client.post("/commands/no_such_command", json={}).status_code == 404)
        script = f"{WORKSPACE}/e2e_browser_script.py"
        try:
            uploaded = client.post("/files/upload-stream", json={"path": script,
                "content_base64": base64.b64encode(b'print("SCRIPT_OK")\n').decode()})
            check("script uploaded via server files API", uploaded.status_code == 200)
            result = client.post("/commands/run", json={"script": "e2e_browser_script.py"})
            check("workspace Python script execution", result.status_code == 200
                  and result.json() == {"result": "SCRIPT_OK\n"})
        finally:
            client.delete("/files", params={"path": script})
        def concurrent_browse(index: int) -> bool:
            title = f"isolated-{index}"
            response = httpx.post(BASE_URL + "/commands/browse", timeout=180,
                json={"url": "data:text/html,<title>" + title + "</title><h1>ok</h1>", "action": "extract"})
            return response.status_code == 200 and response.json()["result"]["title"] == title
        with ThreadPoolExecutor(max_workers=2) as pool:
            check("concurrent requests have independent browsers", all(pool.map(concurrent_browse, range(2))))
    print(f"SUMMARY: {PASSED} PASS, {FAILED} FAIL, 0 SKIP", flush=True)
    return 1 if FAILED else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"[FAIL] acceptance aborted ({type(exc).__name__}); response content omitted", flush=True)
        sys.exit(1)
