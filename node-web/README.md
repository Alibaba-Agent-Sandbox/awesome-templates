# node-web

[中文](README.zh-CN.md)

## What it does

Runs one real Node HTTP application per sandbox. `serve` starts a JavaScript entry point; `start` and `dev` run package scripts in the background. Readiness requires HTTP 2xx/3xx from the owned child. `status`, `request`, `logs`, and `stop` inspect and manage that service. A dependency-free `index.js` is included for a first request.

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a6`, installed directly by the Dockerfile.

Alibaba base `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>` supplies Node 20 and Python 3.13. Deployment resolves the placeholders to `cn-hangzhou` / `v0.0.49` unless configured otherwise.  There are no additional npm dependencies. Work directory `/home/user/app`; non-root `user`; generation 2. Platform `start_cmd` runs the server on 9000 and `ready_cmd` runs its healthcheck; no Docker CMD/ENTRYPOINT is added.

## Problem solved

A successful spawn or open TCP port does not prove an application works. This template checks HTTP, drains stdout/stderr continuously, retains bounded service logs, and stops the npm launcher together with its Node children. `build` executes the application's actual build script and reports a nonzero exit as a failure.

## Quick start (CLI)

CLI, SDK and HTTP are alternative ways to use the same application. Choose one for the task. Examples may write files, create projects or start services; do not repeat the full example on the same instance without cleaning its previous outputs.

Install the CLI/Python SDK and configure your platform with the [usage guide](../docs/using-templates.md#installation). The platform API key creates sandboxes; `ABX_SERVER_TOKEN` independently protects this template application. Run the following in your own terminal; cloning this repository is unnecessary.

These template commands require no model, model endpoint or model API key.

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ABX_HTTP_TIMEOUT=450
abx template launch Alibaba-Agent-Sandbox/awesome-templates//node-web --sandbox-timeout 1800 --yes
# Paste the sandbox ID from the launch output
export SANDBOX_ID='paste-id-from-launch-output'
abx sandbox command list "$SANDBOX_ID"
```

```bash
abx run "$SANDBOX_ID" serve --json-args '{"entry":"index.js","port":3000}'
abx run "$SANDBOX_ID" request --json-args '{"path":"/"}'
```

Returns the sample application HTTP status and body containing `node-web ready`.

`--sandbox-timeout 1800` gives the instance a 30-minute lifetime for the task and artifact export. `ABX_HTTP_TIMEOUT` controls local HTTP waiting and does not extend that lifetime. Delete the instance when finished.

For OpenSandbox, set `ABX_PROVIDER=opensandbox` and configure its [provider guide](https://github.com/Alibaba-Agent-Sandbox/awesome-providers/blob/main/opensandbox/docs/README.md). Keep the same provider selected for subsequent CLI and Python calls.

## Quick start (Python SDK)

In your virtual environment, run `python -m pip install agent-sandbox-client==0.4.0a6`.

After launching above and setting `SANDBOX_ID`, save this as `use_template.py` and run `python3 use_template.py`. It connects to the same instance instead of creating another sandbox. Prepare any input file locally as shown above.

```python
import asyncio
import os
from pathlib import Path
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.connect(
        os.environ["SANDBOX_ID"], provider=os.environ["ABX_PROVIDER"]
    )
    try:
        client = await sb.application_client(
            9000, token=os.environ["ABX_SERVER_TOKEN"], timeout=450
        )
        try:
            await client.commands.run('serve', entry='index.js', port=3000)
            result = await client.commands.run('request', path='/')
            print(result)
        finally:
            try:
                await client.commands.run('stop')
            finally:
                await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

The SDK returns the command value; it unwraps the HTTP `result` envelope. Closing the client does not delete the sandbox.

## Quick start (HTTP POST)

Resolve port 9000 on the same instance with the [HTTP calling example](../docs/using-templates.md#cli-sdk-and-http). Preserve gateway headers, URL path and query before adding the independent application authentication.

First call, in order:

- `POST /commands/serve` with `{"entry": "index.js", "port": 3000}`.

`POST /commands/request`

```json
{
  "path": "/"
}
```

Use `Content-Type: application/json` and application authentication as described in the shared guide. The request body is the direct argument object, without an `args` wrapper. Success returns `{"result": ...}` with the value described above. Set the HTTP client wait to 450 seconds, separately from the command execution deadline. Responses are buffered, not event streams. Errors: 400 invalid arguments, 401 authentication, 404 unknown command, 500 execution failure.

After use, call:

- `POST /commands/stop` with `{}`.

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
| `NODE_ENV` | `production` | Passed to application processes; shipped recipe selects production |
| `PORT` | `3000` | Sample default; each launch overrides with the `port` argument |
| `HOST` | set to `0.0.0.0` by launch | Hint to compatible application servers; application must honor it |
| `WORKSPACE` | unset | Default application working directory |
| `ABX_SERVER_PORT` | `9000` | Local command server port |
| `ABX_SERVER_TOKEN` | empty | Export an independent application token before the template launch; separate from model and gateway credentials |

No model/cloud key is needed by these commands. Keep secret values out of source, images and logs. Inject them only through authorized runtime configuration; do not log environment variables. App stdout is user controlled and can contain secrets: applications must redact before logging, and logs must not be attached to public issues without review.

The working directory is `/home/user/app`. Artifacts remain on the sandbox disk; export anything needed before deleting the instance. Delete only your own instance and the prepared template/image identified by its launch receipt.

```bash
abx run "$SANDBOX_ID" stop --json-args '{}'
abx kill "$SANDBOX_ID"
```

`abx kill` deletes the sandbox, not reusable prepared templates or images. Follow the [cleanup guide](../docs/using-templates.md#cli-sdk-and-http) for resources created by your launch.

## Resources

2 vCPU, 2048 MB memory. Port 9000 is the command API; 3000 is the sample service. Custom ports need provider gateway support. No privileged operations, Docker-in-sandbox, GPU, KVM, or browser. Application dependencies and artifacts consume the provider's rootfs budget (about 10 GB on Express).

## Contributing

To improve this template, see the [contribution guide](../CONTRIBUTING.md), [template specification](../docs/template-spec.md) and [design notes](../docs/design/node-web.md).

## Issues

Track this template in [awesome-templates#29](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/29). Search existing issues before filing. Include sanitized command arguments, expected/actual behavior, test level, provider, generation 2 and SDK commit. Template problems go to awesome-templates; server/client bugs to [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues) with `[templates]`; CLI problems to [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues) with the same prefix. Never attach `.env`, access tokens or unreviewed application logs.

## License

Apache-2.0; see the repository [LICENSE](../LICENSE).
