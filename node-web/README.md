# node-web

## What it does

Runs one real Node HTTP application per sandbox. `serve` starts a JavaScript entry point; `start` and `dev` run package scripts in the background. Readiness requires HTTP 2xx/3xx from the owned child. `status`, `request`, `logs`, and `stop` inspect and manage that service. A dependency-free `index.js` is included for a first request.

## Stack

Alibaba base `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>` supplies Node 20 and Python 3.13. Deployment resolves the placeholders to `cn-hangzhou` / `v0.0.49` unless configured otherwise. The server fallback is pinned to python-sdk commit `35da216a300f1e2e84254a1cf4b4a7ea98681505`; a CLI-injected server wheel takes precedence. There are no additional npm dependencies. Work directory `/home/user/app`; non-root `user`; generation 2. Platform `start_cmd` runs the server on 9000 and `ready_cmd` runs its healthcheck; no Docker CMD/ENTRYPOINT is added.

## Problem solved

A successful spawn or open TCP port does not prove an application works. This template checks HTTP, drains stdout/stderr continuously, retains bounded service logs, and stops the npm launcher together with its Node children. `build` executes the application's actual build script and reports a nonzero exit as a failure.

## Quick start (CLI)

With the provider already configured, deploy from the repository root:

```bash
abx template deploy ./node-web -y
abx create --template <template-id> -y
abx run <sandbox-id> serve --json-args '{"entry":"index.js","port":3000}'
abx run <sandbox-id> request --json-args '{"path":"/"}'
abx run <sandbox-id> logs --json-args '{"max_bytes":16384}'
abx run <sandbox-id> stop
abx kill <sandbox-id> -y
abx template delete <template-id> -y
```

The request returns `status_code: 200` and `body: "node-web ready\n"`. Upload your application and its locked dependencies before using a custom `entry` or `cwd`. `start`/`dev`/`build` require your `package.json` scripts; the bundled sample needs none. A service must honor `PORT` and bind to `0.0.0.0` for a gateway preview. Preview its provider URL for port 3000; the command API uses port 9000.

## Quick start (Python SDK)

The client distribution is `agent-sandbox-client` (import `agent_sandbox`). Until the matching release is available, use the [paired, pinned source installation](../docs/python-client-installation.md).

```python
import asyncio
from agent_sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=300)
    try:
        print(await sb.run("serve", entry="index.js", port=3000, timeout_s=20))
        result = await sb.run("request", path="/")
        assert result["status_code"] == 200
        assert result["body"] == "node-web ready\n"
        print(sb.network.get_url(3000))
        print(await sb.run("logs", max_bytes=16384))
        await sb.run("stop")
    finally:
        await sb.kill()

asyncio.run(main())
```

`sb.run` returns the value inside the HTTP `result` wrapper. `sb.commands.run` is the separate shell/process API. For long builds, set an HTTP `timeout` greater than `timeout_s`, e.g. `await sb.run("build", cwd="/home/user/app/my-app", timeout_s=120, timeout=150)`. `timeout_s` is the execution/readiness deadline; the client's `timeout` only limits the request and does not guarantee cancellation. Use process APIs for reconnectable jobs.

## Quick start (HTTP POST)

Set `SERVER_URL` to the provider's sandbox port-9000 URL (`sb.network.get_url(9000)`), or `http://127.0.0.1:9000` for local L0. The following requests use direct JSON parameter objects, without an `args` wrapper:

```bash
curl --fail-with-body -X POST "$SERVER_URL/commands/serve" \
  -H 'Content-Type: application/json' -d '{"entry":"index.js","port":3000,"timeout_s":20}'
curl --fail-with-body -X POST "$SERVER_URL/commands/request" \
  -H 'Content-Type: application/json' -d '{"path":"/"}'
curl --fail-with-body -X POST "$SERVER_URL/commands/stop" \
  -H 'Content-Type: application/json' -d '{}'
```

The request response is `{"result":{"status_code":200,"body":"node-web ready\n","truncated":false}}`. The serve response includes `pid`, `port`, `status`, `cwd`, and `http_status`; stop returns `status` and `pid`.

If `ABX_SERVER_TOKEN` is set inside the sandbox, add `Authorization: Bearer $ABX_SERVER_TOKEN` or `X-Access-Token: $ABX_SERVER_TOKEN` to **every** command request. For Python, use `sb.server_at(9000, token=server_token).run(...)` with the same token supplied at sandbox creation. Provider gateway authentication is separate: add the header required by the chosen provider (Express uses `X-Access-Token: $SANDBOX_ACCESS_TOKEN`); when both are needed, put the server token in `Authorization` and the gateway token in `X-Access-Token`. Obtain both from your authorized runtime configuration; examples contain no real values.

Errors use `{"error":"...","type":"..."}`: 400 for missing/mistyped/unknown arguments, 401 for server authentication, 404 for an unknown named command, and 500 for command execution failures (including out-of-range values, unavailable ports, failed builds and readiness deadlines). All named responses are buffered. A service's own HTTP 404 is returned in `request.result.status_code`, with command HTTP 200.

## Command reference

All parameters are optional. `cwd` is a string defaulting to empty: use `WORKSPACE`, then `/home/user/app`, then the server working directory if that default path is absent. Explicit `cwd` must exist. Start commands share `port: int = 3000` (1024–65535, excluding the command-server port), `ready_path: str = "/"` (local absolute path, no `//` or CR/LF), and `timeout_s: int = 20` (1–120 seconds).

| Command | Parameters | Returns / executed argv |
|---|---|---|
| `serve` | shared parameters; `entry: str = "index.js"`; `cwd: str = ""` | Running metadata after HTTP readiness; `node <resolved-entry>` in `cwd` |
| `start` | shared parameters; `cwd: str = ""` | Running metadata; `npm start` |
| `dev` | shared parameters; `cwd: str = ""` | Running metadata; `npm run dev` |
| `status` | none | `status`, `pid`, and `http_ready`; after a launch also `port`, `exit_code`, `http_status` |
| `stop` | none | `status: stopped`, `pid`; SIGTERM then SIGKILL to owned process group; safe to repeat |
| `logs` | `max_bytes: int = 16384`, 1–131072 | `output`, `max_bytes`; latest merged stdout/stderr, retained after stop |
| `request` | `path: str = "/"`, local path only; `timeout_s: int = 5`, 1–30 | Real loopback GET: `status_code`, UTF-8 `body` (up to 65536 bytes), `truncated`; no redirect following |
| `build` | `cwd: str = ""`; `timeout_s: int = 120`, 1–600 | `npm run build`; `exit_code: 0`, latest 131072 bytes of `output`, `truncated`; raises on failure/timeout |
| `smoke` | none | Starts bundled sample on 3000, asserts exact HTTP response, stops in `finally`, returns `node-web ready` |

One service can run at a time; a second start fails until `stop`. Readiness tests the configured path, accepts only HTTP 200–399, and fails if the child exits. `request` probes only the managed loopback port. Logs rotate at 1 MiB (two files maximum) in a private temporary directory. `build` uses a temporary output file and removes it after execution; output returned to callers is bounded. Very verbose builds can use temporary disk space before completion. The manager is in memory; restarting the command server loses its process registry. Destroying the sandbox is the final cleanup boundary.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `NODE_ENV` | `production` | Passed to application processes; set at sandbox creation for development |
| `PORT` | `3000` | Sample default; each launch overrides with the `port` argument |
| `HOST` | set to `0.0.0.0` by launch | Hint to compatible application servers; application must honor it |
| `WORKSPACE` | unset | Default application working directory |
| `ABX_SERVER_PORT` | `9000` | Local command server port |
| `ABX_SERVER_TOKEN` | empty | Optional command-server authentication; secret name declared with an empty value |

No model/cloud key is needed by these commands. Keep secret values out of source, images and logs. Inject them only through authorized runtime configuration; do not log environment variables. App stdout is user controlled and can contain secrets: applications must redact before logging, and logs must not be attached to public issues without review.

## Resources

2 vCPU, 2048 MB memory. Port 9000 is the command API; 3000 is the sample service. Custom ports need provider gateway support. No privileged operations, Docker-in-sandbox, GPU, KVM, or browser. Application dependencies and artifacts consume the provider's rootfs budget (about 10 GB on Express).

## Verified

No provider has a passing run recorded for this template.

2026-10-16 local L0 passed all 60 assertions with real Node 22.22.2, isolated npm 10.9.4, agent-sandbox-server 0.3.0 and httpx 0.28.1: HTTP API discovery, 4 MiB pre-readiness output, real HTTP requests, stderr logs, npm build artifact, npm start/dev and process-group stop/rebind, build nonzero/timeout and readiness failure. This is a local host run; it does not establish the Node 20 image build or cloud behavior. L1 is pending because Docker is absent. L2/L4 are pending; `tested_on` remains empty. No model call is required for this service template.

## Express source-runtime verification

On 2026-10-16, all 60 external HTTP assertions passed against the patched source on an owned Express base sandbox with its actual Node.js 20 runtime. The run covers bundled smoke, uploaded application build/start/dev, HTTP readiness, bounded logs, shutdown, port reuse and cleanup. The owned instance was destroyed. [JSON evidence](evidence/runtime-express-2026-10-16.json) records source/config/fixture/wheel hashes; [HTTP results](evidence/runtime-express-2026-10-16.log) record the assertions. This does not establish a Dockerfile build or deployment of a new template image; `tested_on` remains empty. See [the runner](../docs/express-source-runtime.md).

## Secondary development

The HTTP acceptance script emits one `[PASS]` or `[FAIL]` line per assertion.
Acceptance consumers require exit0, no failures and a positive pass count; exit0
with zero recognized assertions is rejected. Run
`python -m pytest --import-mode=importlib -q node-web/test_http_output.py` to exercise
the actual local server/Node/npm full60-assertion suite and the same strict result
counter. A separate real HTTP503 fixture checks nonzero/countable failure. Tests
use an owned temporary npm cache and keep the original HOME; no installation or
model call is required. The earlier unbracketed-output run remains rejected by
the image acceptance counter and is not retroactively relabeled as a pass.

Upload a project beneath `/home/user/app`, include its dependency lockfile, and install exact versions when building a derivative image (`npm ci` against the committed lockfile). Keep package installs before the final `COPY commands.py`, remove the npm cache in the same image layer, retain the pinned server, Alibaba base, non-root user and generation-2 start/ready commands. Do not add Docker CMD/ENTRYPOINT. Express/Fastify applications use `serve`, or define `start`/`dev`/`build` scripts. This template does not install a framework or generate a Next/Vite project.

## Contributing

Read [CONTRIBUTING.md](../CONTRIBUTING.md), the [template spec](../docs/template-spec.md), and [design](../docs/design/node-web.md). Run `python3 scripts/check_template.py node-web`, then `python3 scripts/run_local_e2e.py` from the repository root with server SDK, httpx, PyYAML, Node and npm available. The suite runs real processes and asserts outputs, not mocks. With Docker and authorized Express access, run `python3 scripts/express_e2e.py node-web`; only a successful run may add provider evidence. Keep `tested_on` and Verified empty until then. Cross-review process lifecycle and failure cases before merging.

## Issues

Track this template in [awesome-templates#29](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/29). Search existing issues before filing. Include sanitized command arguments, expected/actual behavior, test level, provider, generation 2 and SDK commit. Template problems go to awesome-templates; server/client bugs to [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues) with `[templates]`; CLI problems to [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues) with the same prefix. Never attach `.env`, access tokens or unreviewed application logs.

## License

Apache-2.0; see the repository [LICENSE](../LICENSE).
