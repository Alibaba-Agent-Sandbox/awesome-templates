# next-app

Pinned Next.js16.4.2, React/React DOM19.3.1 and Vite8.3.4 frontend scaffolds and preview servers.

## What it does

Create a fresh minimal Next.js or Vite application, serve real source edits, inspect a bounded log tail and stop owned workers. One development server at a time; command API9000, Next3000, Vite5173. No Vercel publishing or claimed HMR/WebSocket certification.

## Stack

Alibaba base `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>` resolves to region and defaultv0.0.49. Observed Node20.20.2 meets the verified engine requirements. `npm ci` installs committed package-lock.json integrity pins; runtime never downloads packages. Dependency licenses/notices remain in node_modules. Server fallback: python-sdk commit e2cb27e24fde0a67112f82b8d44af463445a5d1a; deploy-injected wheel wins. Generation2, USER user, /home/user/app, platform-managed start/health commands; no Docker CMD/ENTRYPOINT.

## Problem solved

Provide concrete front-end scaffolds and persistent previews beyond generic Node execution, with reproducible installation and explicit resource ownership.

## Quick start (CLI)

Follow the [usage guide](../docs/using-templates.md#installation) to install the clients, configure the provider and set an independent `ABX_SERVER_TOKEN`. From this repository's root, launch the application and retain its sandbox ID. Replace `<sandbox-id>` below with that ID.

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./next-app --workflow application --yes
abx run <sandbox-id> toolchain_versions --json-args '{}'
```

`template launch` prepares and starts this instance's application. For OpenSandbox, set `ABX_PROVIDER=opensandbox` above and use `provider="opensandbox"` in Python. See the [complete calling flow](../docs/using-templates.md#cli-sdk-and-http) for OpenSandbox configuration, provider selection on every call and owned-resource cleanup. The next examples reuse the same running instance.

## Quick start (Python SDK)

Install `agent-sandbox-client` and follow the [Python connection example](../docs/using-templates.md#cli-sdk-and-http), using `ProviderSandbox.connect` and `application_client` with the independent application token. Replace the command call inside that example's `try` block with:

```python
print(await client.commands.run('toolchain_versions'))
```

Keep the guide's connection and close steps. `sb.commands.run` executes a process; `client.commands.run` calls this template's named commands. Business commands, arguments and limits are listed in the command reference below.

## Quick start (HTTP POST)

Follow the [HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserve gateway headers, path and query parameters, and set the independent application token. Change the request to `POST /commands/toolchain_versions`, with `Content-Type: application/json` and this direct argument object:

```json
{}
```

Expected response for this check:

```json
{"result": {"next": "16.4.2", "react": "19.3.1", "react-dom": "19.3.1", "vite": "8.3.4"}}
```

`result` is buffered, not an event stream. Missing or mistyped arguments return 400, failed authentication 401, unknown commands 404, and execution errors 500. Set the HTTP wait and command deadline separately; a client timeout does not guarantee cancellation.

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

Version1.1.0 adds allowed_host for Vite's exact SDK-forwarded hostname. The default empty value preserves localhost-only host authorization; pass urlsplit((await sb.network.resolve(5173))[0]).hostname from the SDK. It sets only the upstream-supported __VITE_ADDITIONAL_SERVER_ALLOWED_HOSTS, verified in pinned Vite8.3.4 source and [official server options](https://vite.dev/config/server-options#server-allowedhosts). Wildcards, leading-dot suffixes, schemes, ports, credentials, commas and empty DNS labels are refused. Next does not accept this Vite-only setting. Runtime1.0.0's actual forwarded Vite403 attempt remains a failure;the completed1.1.0 image/forwarded acceptance is linked below. No Host rewrite or global allow-all mode is used.

## Configuration

| Name | Default | Purpose |
|---|---|---|
| ABX_SERVER_TOKEN | empty | Export an independent application token before the application workflow launch; separate from model and gateway credentials |
| ABX_SERVER_PORT | 9000 | local server port |
| WORKSPACE | /home/user/app | existing workspace root |
| NEXT_APP_TOOLCHAIN | /opt/next-app | trusted pinned toolchain; local tests may select the installed source directory |

Development server environment contains only Node PATH, isolated temporary HOME, locale, telemetry opt-out and ownership marker. No cloud/model keys are inherited. The preview application itself has no password authentication; use provider access controls. Logs can include application output: do not publish raw log tails containing private data.

## Resources

2vCPU,2048MB; platform rootfs about10GiB; ports9000/3000/5173. No Docker/KVM/display required. Commands require Linux pidfds and procfs for identity-safe cleanup. Owner-marked detached workers and the unreaped process group are stopped; kernel listener absence is checked before cleanup succeeds.

## Verified

See [test results and scope](../docs/using-templates.md#evidence-and-providers). The dated records below identify the tested input and entry point.

## Secondary development

Edit generated source through SDK files. Keep framework packages pinned and regenerate the lockfile when intentionally upgrading. See [official Next installation](https://nextjs.org/docs/app/getting-started/installation) and [Vite guide](https://vite.dev/guide/). Development servers execute application code; this wrapper is not an additional sandbox security boundary.

## Contributing

[CONTRIBUTING.md](../CONTRIBUTING.md), [template spec](../docs/template-spec.md), and [design](../docs/design/next-app.md). Run targeted real-process tests, complete HTTP L0, actual image L1 and cloud L2 before provider qualification. Preserve failed attempts and independent owned cleanup evidence.

## Issues

[Template issues](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/54), [Python SDK/server](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), [CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). SDK/CLI reports use title prefix [templates].

## License

Repository code Apache-2.0: [LICENSE](../LICENSE). Next, React and Vite are MIT; retained package notices and upstream-pins.json record the installed sources. Transitive license notices remain installed.

For operator browser preview when FC serves HTML as an attachment, use the [SDK local relay](../docs/preview-proxy.md) after starting the owned app: python scripts/preview_proxy.py --sandbox-id <owned-sandbox-id> --remote-port 3000 (Next) or --remote-port 5173 (Vite). Keep the exact Vite allowed_host above. The relay borrows that sandbox; stop the relay and explicitly stop/kill owned app resources. This documented Next/Vite browser route is source checked; its browser/HMR behavior has not been separately qualified.

### Additional current-version platform-step acceptance

[Actual native steps](evidence/express-2026-10-20T130712Z.json): official READY, Python SDK creation, current CLI/SDK smoke and independently confirmed owned sandbox/template cleanup. [Full external HTTP](evidence/full-http-steps-2026-10-20T130712Z.json): 6 PASS / 0 FAIL / 0 SKIP.
