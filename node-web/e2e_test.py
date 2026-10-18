#!/usr/bin/env python3
"""Real Node service/build lifecycle over the server HTTP API; no mocks or keys."""
from __future__ import annotations

import base64
import json
import os
from pathlib import PurePosixPath
import sys
import uuid

import httpx

BASE_URL = os.environ.get("E2E_BASE_URL", "http://127.0.0.1:9000").rstrip("/")
WORKSPACE = os.environ.get("E2E_WORKSPACE", "/home/user/app")
PASSED = 0


def check(condition: bool, label: str) -> None:
    global PASSED
    print(f"[{'PASS' if condition else 'FAIL'}] {label}", flush=True)
    if not condition:
        raise AssertionError(label)
    PASSED += 1


def main() -> int:
    directory = str(PurePosixPath(WORKSPACE) / ("abx_e2e_node_web_" + uuid.uuid4().hex))
    # Emit 4 MiB *before* listening and respect Node's stdout backpressure. An
    # unconsumed Popen PIPE prevents readiness here instead of silently passing.
    app = '''const http = require('node:http');
const {once} = require('node:events');
(async () => {
 for (let i = 0; i < 512; i++) {
   if (!process.stdout.write('x'.repeat(8192))) await once(process.stdout, 'drain');
 }
 console.error('BOOT_DONE');
 http.createServer((req, res) => {
   if (req.url === '/missing') {res.writeHead(404); res.end('missing'); return;}
   res.writeHead(200); res.end('real-node-response');
 }).listen(Number(process.env.PORT), '0.0.0.0');
})();
'''
    token = os.environ.get("E2E_TOKEN") or os.environ.get("ABX_SERVER_TOKEN", "")
    headers = {"Authorization": "Bearer " + token} if token else {}
    with httpx.Client(base_url=BASE_URL, timeout=45, headers=headers) as client:
        def call(name: str, args: dict | None = None, expected: int = 200):
            response = client.post(f"/commands/{name}", json=args or {})
            check(response.status_code == expected, f"{name}: HTTP {expected}")
            body = response.json()
            return body.get("result") if expected == 200 else body

        def upload(name: str, text: str) -> None:
            response = client.post("/files/upload-stream", json={
                "path": f"{directory}/{name}",
                "content_base64": base64.b64encode(text.encode()).decode(),
            })
            check(response.status_code == 200, f"upload {name}")

        health = client.get("/health")
        check(health.status_code == 200 and health.json()["status"] == "ok", "server health")
        names = {item["name"] for item in client.get("/commands").json()["commands"]}
        check({"serve", "start", "dev", "build", "status", "stop", "logs", "request", "smoke"} <= names,
              "complete command discovery")
        check(client.post("/files/mkdir", json={"path": directory}).status_code == 200, "workspace mkdir")
        try:
            call("stop")
            check(call("status")["status"] == "stopped", "initial stopped")
            call("serve", {"cwd": directory, "entry": "missing.js"}, 500)
            call("serve", {"port": "not-a-number"}, 400)
            call("logs", {"max_bytes": 0}, 500)
            call("not_a_command", expected=404)
            upload("index.js", app)
            upload("package.json", json.dumps({"private": True, "scripts": {
                "start": "node index.js", "dev": "node index.js", "build": "node build.js"}}))
            upload("build.js", "require('node:fs').writeFileSync('build-artifact.txt', 'built-by-node');console.log('built');")
            result = call("serve", {"cwd": directory, "port": 39671, "timeout_s": 15})
            check(result["status"] == "running" and result["http_status"] == 200, "high-output HTTP readiness")
            response = call("request")
            check(response["status_code"] == 200 and response["body"] == "real-node-response", "actual Node response")
            check(call("request", {"path": "/missing"})["status_code"] == 404, "application HTTP error preserved")
            check(call("status")["http_ready"] is True, "status probes HTTP")
            check("BOOT_DONE" in call("logs", {"max_bytes": 131072})["output"], "4 MiB drained; stderr available")
            check(len(call("logs", {"max_bytes": 4096})["output"]) <= 4096, "bounded log response")
            call("request", {"path": "//other-host/"}, 500)
            call("serve", {"cwd": directory, "port": 39672}, 500)
            # Independent probe via the server process API, not the template's
            # request helper: proves Node's response over an actual socket.
            probe = "node -e \"require('http').get('http://127.0.0.1:39671/',r=>r.pipe(process.stdout))\""
            response = client.post("/shell", json={"command": probe})
            check(response.status_code == 200 and response.json()["stdout"] == "real-node-response", "independent socket request")
            call("stop")
            check(call("status")["status"] == "stopped", "serve process stopped")
            call("request", expected=500)
            build = call("build", {"cwd": directory})
            check(build["exit_code"] == 0 and "built" in build["output"], "real npm build")
            artifact = client.get("/files/download-stream", params={"path": directory + "/build-artifact.txt"})
            check(artifact.status_code == 200 and base64.b64decode(artifact.json()["content_base64"]) == b"built-by-node",
                  "independently read build artifact")
            for name in ("start", "dev"):
                result = call(name, {"cwd": directory, "port": 39671, "timeout_s": 15})
                check(result["status"] == "running", f"npm {name} starts in background")
                check(call("request")["body"] == "real-node-response", f"npm {name} HTTP response")
                call("stop")
                # Rebinding the same port in the next iteration proves children
                # of the npm launcher were stopped, not merely the npm parent.
            upload("build.js", "process.exit(7)")
            call("build", {"cwd": directory}, 500)
            upload("build.js", "setTimeout(()=>{}, 10000)")
            call("build", {"cwd": directory, "timeout_s": 1}, 500)
            upload("no-http.js", "require('net').createServer(()=>{}).listen(Number(process.env.PORT), '0.0.0.0')")
            call("serve", {"entry": "no-http.js", "cwd": directory, "port": 39671, "timeout_s": 1}, 500)
            check(call("status")["status"] == "stopped", "TCP-only listener fails HTTP readiness and is killed")
            call("serve", {"entry": "index.js", "cwd": directory, "port": 39671})
            call("stop")
            call("stop")
            check(call("smoke") == "node-web ready", "bundled sample real HTTP smoke")
        finally:
            call("stop")
            # Remove only the test-owned directory, preserving user application.
            response = client.delete("/files", params={"path": directory, "recursive": "true"})
            check(response.status_code == 200, "workspace cleanup")
        print(f"node-web: {PASSED} passed; L0 only", flush=True)
        return 0


if __name__ == "__main__":
    sys.exit(main())
