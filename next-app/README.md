# next-app

[中文](README.zh-CN.md)

## What it does

Create a fresh minimal Next.js or Vite application, serve real source edits, inspect a bounded log tail and stop owned workers. One development server at a time; command API9000, Next3000, Vite5173. No Vercel publishing or claimed HMR/WebSocket certification.

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a6`, installed directly by the Dockerfile.

Alibaba base `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>` resolves to region and defaultv0.0.49. Observed Node20.20.2 meets the verified engine requirements. `npm ci` installs committed package-lock.json integrity pins; runtime never downloads packages. Dependency licenses/notices remain in node_modules.  Generation2, USER user, /home/user/app, platform-managed start/health commands; no Docker CMD/ENTRYPOINT.

## Problem solved

Provide concrete front-end scaffolds and persistent previews beyond generic Node execution, with reproducible installation and explicit resource ownership.

## Quick start (CLI)

CLI, SDK and HTTP are alternative ways to use the same application. Choose one for the task. Examples may write files, create projects or start services; do not repeat the full example on the same instance without cleaning its previous outputs.

Install the CLI/Python SDK and configure your platform with the [usage guide](../docs/using-templates.md#installation). The platform API key creates sandboxes; `ABX_SERVER_TOKEN` independently protects this template application. Run the following in your own terminal; cloning this repository is unnecessary.

These template commands require no model, model endpoint or model API key.

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ABX_HTTP_TIMEOUT=450
abx template launch Alibaba-Agent-Sandbox/awesome-templates//next-app --sandbox-timeout 1800 --yes
# Paste the sandbox ID from the launch output
export SANDBOX_ID='paste-id-from-launch-output'
abx sandbox command list "$SANDBOX_ID"
```

```bash
abx run "$SANDBOX_ID" scaffold --json-args '{"kind":"next","path":"preview-app"}'
abx run "$SANDBOX_ID" dev_start --json-args '{"kind":"next","path":"preview-app","timeout_s":120}'
```

Returns `running: true`, `port: 3000`. Resolve port 3000 to view `ABX_NEXT_PREVIEW`; source files remain in `preview-app/`.

Resolve the Next.js preview with `await sb.network.resolve(3000)`, preserving its path, query and gateway headers; use the [preview guide](../docs/preview-proxy.md) when needed. The app has no built-in login; use provider access controls. Vite uses `kind="vite"` and port 5173; if Host validation rejects the gateway, pass that exact gateway hostname as `allowed_host`, not a wildcard.

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
            await client.commands.run('scaffold', kind='next', path='preview-app')
            result = await client.commands.run('dev_start', kind='next', path='preview-app', timeout_s=120)
            print(result)
        finally:
            try:
                await client.commands.run('dev_stop')
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

- `POST /commands/scaffold` with `{"kind": "next", "path": "preview-app"}`.

`POST /commands/dev_start`

```json
{
  "kind": "next",
  "path": "preview-app",
  "timeout_s": 120
}
```

Use `Content-Type: application/json` and application authentication as described in the shared guide. The request body is the direct argument object, without an `args` wrapper. Success returns `{"result": ...}` with the value described above. Set the HTTP client wait to 450 seconds, separately from the command execution deadline. Responses are buffered, not event streams. Errors: 400 invalid arguments, 401 authentication, 404 unknown command, 500 execution failure.

After use, call:

- `POST /commands/dev_stop` with `{}`.

## Command reference

| Command | Parameters | Returns |
|---|---|---|
| preview_self_test | none / 无 | NEXT_VITE_PREVIEW_OK; actual Next/Vite pages, owned workers/project cleanup |
| toolchain_versions | none | actual installed next/react/react-dom/vite version map |
| scaffold | kind: next or vite, default next; path: new single workspace directory name, default preview-app | {path,kind} |
| dev_start | kind: next or vite, default next; path: matching scaffold, default preview-app; timeout_s:1..180, default120; allowed_host:str="", one exact DNS hostname for Vite only | {port,kind,running:true} |
| dev_status | none | {running:false} or {port,kind,path,running:true} |
| dev_logs | tail_bytes:1..8192, default4096 | bounded buffered log tail |
| dev_stop | none | {running:false} after owned process/listener absence |

Next uses local next dev --webpack --hostname0.0.0.0 --port3000. Vite uses local vite --host0.0.0.0 --port5173 --strictPort. Literal argv; no shell interpolation. Existing directories and symlink/traversal paths are rejected. The controlled node_modules symlink points to the immutable preinstalled toolchain. Project source/build cache remain after stop; remove them explicitly when no longer needed.

Use allowed_host for Vite's exact SDK-forwarded hostname. The default empty value preserves localhost-only host authorization; pass urlsplit((await sb.network.resolve(5173))[0]).hostname from the SDK. It sets only the upstream-supported __VITE_ADDITIONAL_SERVER_ALLOWED_HOSTS, verified in pinned Vite8.3.4 source and [official server options](https://vite.dev/config/server-options#server-allowedhosts). Wildcards, leading-dot suffixes, schemes, ports, credentials, commas and empty DNS labels are refused. Next does not accept this Vite-only setting. No Host rewrite or global allow-all mode is used.

## Configuration

| Name | Default | Purpose |
|---|---|---|
| ABX_SERVER_TOKEN | empty | Export an independent application token before the template launch; separate from model and gateway credentials |
| ABX_SERVER_PORT | 9000 | local server port |
| WORKSPACE | /home/user/app | existing workspace root |
| NEXT_APP_TOOLCHAIN | /opt/next-app | trusted pinned toolchain; local tests may select the installed source directory |

Development server environment contains only Node PATH, isolated temporary HOME, locale, telemetry opt-out and ownership marker. No cloud/model keys are inherited. The preview application itself has no password authentication; use provider access controls. Logs can include application output: do not publish raw log tails containing private data.

The working directory is `/home/user/app`. Artifacts remain on the sandbox disk; export anything needed before deleting the instance. Delete only your own instance and the prepared template/image identified by its launch receipt.

```bash
abx run "$SANDBOX_ID" dev_stop --json-args '{}'
abx kill "$SANDBOX_ID"
```

`abx kill` deletes the sandbox, not reusable prepared templates or images. Follow the [cleanup guide](../docs/using-templates.md#cli-sdk-and-http) for resources created by your launch.

## Resources

2vCPU,2048MB; platform rootfs about10GiB; ports9000/3000/5173. No Docker/KVM/display required. Commands require Linux pidfds and procfs for identity-safe cleanup. Owner-marked detached workers and the unreaped process group are stopped; kernel listener absence is checked before cleanup succeeds.

## Contributing

To improve this template, see the [contribution guide](../CONTRIBUTING.md), [template specification](../docs/template-spec.md) and [design notes](../docs/design/next-app.md).

## Issues

[Template issues](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/54), [Python SDK/server](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), [CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). SDK/CLI reports use title prefix [templates].

## License

Repository code Apache-2.0: [LICENSE](../LICENSE). Next, React and Vite are MIT; retained package notices and upstream-pins.json record the installed sources. Transitive license notices remain installed.

For operator browser preview when FC serves HTML as an attachment, use the [SDK local relay](../docs/preview-proxy.md) after starting the owned app: python scripts/preview_proxy.py --sandbox-id <owned-sandbox-id> --remote-port 3000 (Next) or --remote-port 5173 (Vite). Keep the exact Vite allowed_host above. The relay borrows that sandbox; stop the relay and explicitly stop/kill owned app resources. This documented Next/Vite browser route is source checked; its browser/HMR behavior has not been separately qualified.
