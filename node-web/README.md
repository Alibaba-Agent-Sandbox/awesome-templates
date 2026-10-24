# node-web

## What it does

Runs one real Node HTTP application per sandbox. `serve` starts a JavaScript entry point; `start` and `dev` run package scripts in the background. Readiness requires HTTP 2xx/3xx from the owned child. `status`, `request`, `logs`, and `stop` inspect and manage that service. A dependency-free `index.js` is included for a first request.

## Stack

Alibaba base `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>` supplies Node 20 and Python 3.13. Deployment resolves the placeholders to `cn-hangzhou` / `v0.0.49` unless configured otherwise. The server fallback is pinned to python-sdk commit `35da216a300f1e2e84254a1cf4b4a7ea98681505`; a CLI-injected server wheel takes precedence. There are no additional npm dependencies. Work directory `/home/user/app`; non-root `user`; generation 2. Platform `start_cmd` runs the server on 9000 and `ready_cmd` runs its healthcheck; no Docker CMD/ENTRYPOINT is added.

## Problem solved

A successful spawn or open TCP port does not prove an application works. This template checks HTTP, drains stdout/stderr continuously, retains bounded service logs, and stops the npm launcher together with its Node children. `build` executes the application's actual build script and reports a nonzero exit as a failure.

## Quick start (CLI)

Follow the [usage guide](../docs/using-templates.md#installation) to install the clients, configure the provider and set an independent `ABX_SERVER_TOKEN`. From this repository's root, launch the application and retain its sandbox ID. Replace `<sandbox-id>` below with that ID.

```bash
abx --provider alicloud-express template launch ./node-web --workflow application --yes
abx run <sandbox-id> smoke --json-args '{}'
```

`template launch` prepares and starts this instance's application. See the [complete calling flow](../docs/using-templates.md#cli-sdk-and-http) for OpenSandbox configuration, provider selection on every call and owned-resource cleanup. The next examples reuse the same running instance.

## Quick start (Python SDK)

Install `agent-sandbox-client` and follow the [Python connection example](../docs/using-templates.md#cli-sdk-and-http), using `ProviderSandbox.connect` and `application_client` with the independent application token. Replace the command call inside that example's `try` block with:

```python
print(await client.commands.run('smoke'))
```

Keep the guide's connection and close steps. `sb.commands.run` executes a process; `client.commands.run` calls this template's named commands. Business commands, arguments and limits are listed in the command reference below.

## Quick start (HTTP POST)

Follow the [HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserve gateway headers, path and query parameters, and set the independent application token. Change the request to `POST /commands/smoke`, with `Content-Type: application/json` and this direct argument object:

```json
{}
```

Expected response for this check:

```json
{"result": "node-web ready"}
```

`result` is buffered, not an event stream. Missing or mistyped arguments return 400, failed authentication 401, unknown commands 404, and execution errors 500. Set the HTTP wait and command deadline separately; a client timeout does not guarantee cancellation.

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
| `ABX_SERVER_TOKEN` | empty | Export an independent application token before the application workflow launch; separate from model and gateway credentials |

No model/cloud key is needed by these commands. Keep secret values out of source, images and logs. Inject them only through authorized runtime configuration; do not log environment variables. App stdout is user controlled and can contain secrets: applications must redact before logging, and logs must not be attached to public issues without review.

## Resources

2 vCPU, 2048 MB memory. Port 9000 is the command API; 3000 is the sample service. Custom ports need provider gateway support. No privileged operations, Docker-in-sandbox, GPU, KVM, or browser. Application dependencies and artifacts consume the provider's rootfs budget (about 10 GB on Express).

## Verified

See [test results and scope](../docs/using-templates.md#evidence-and-providers). The dated records below identify the tested input and entry point.

## Historical verification

| Provider | Executed scope | Evidence |
| --- | --- | --- |
| alicloud-express | steps build, official READY, CLI + SDK smoke, independent owned cleanup readback | [2026-10-19](evidence/express-2026-10-19.json) |

This run uses the pinned e2cb27e server-source override matching existing image CI injection; the receipt records exact versions, input hashes and build mode. Only verification metadata changes here; the template stays experimental. Dockerfile L1, full product and real-model acceptance are assessed by their separate records and cannot be inferred from basic smoke.

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

### Agent Sandbox platform steps

From a repository checkout, `python scripts/run_steps_e2e.py node-web` builds and verifies this template through real Express platform steps. See [preparation, credentials, exact build provenance and cleanup](../docs/platform-steps.md). A model-free step smoke does not establish L3.

## Contributing

Read [CONTRIBUTING.md](../CONTRIBUTING.md), the [template spec](../docs/template-spec.md), and [design](../docs/design/node-web.md). Run `python3 scripts/check_template.py node-web`, then `python3 scripts/run_local_e2e.py` from the repository root with server SDK, httpx, PyYAML, Node and npm available. The suite runs real processes and asserts outputs, not mocks. With Docker and authorized Express access, run `python3 scripts/express_e2e.py node-web`; only a successful run may add provider evidence. Keep `tested_on` and Verified empty until then. Cross-review process lifecycle and failure cases before merging.

## Issues

Track this template in [awesome-templates#29](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/29). Search existing issues before filing. Include sanitized command arguments, expected/actual behavior, test level, provider, generation 2 and SDK commit. Template problems go to awesome-templates; server/client bugs to [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues) with `[templates]`; CLI problems to [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues) with the same prefix. Never attach `.env`, access tokens or unreviewed application logs.

## License

Apache-2.0; see the repository [LICENSE](../LICENSE).
