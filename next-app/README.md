# next-app

Pinned Next.js16.4.2, React/React DOM19.3.1 and Vite8.3.4 frontend scaffolds and preview servers.

## What it does

Create a fresh minimal Next.js or Vite application, serve real source edits, inspect a bounded log tail and stop owned workers. One development server at a time; command API9000, Next3000, Vite5173. No Vercel publishing or claimed HMR/WebSocket certification.

## Stack

Alibaba base `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>` resolves to region and defaultv0.0.49. Observed Node20.20.2 meets the verified engine requirements. `npm ci` installs committed package-lock.json integrity pins; runtime never downloads packages. Dependency licenses/notices remain in node_modules. Server fallback: python-sdk commit e2cb27e24fde0a67112f82b8d44af463445a5d1a; deploy-injected wheel wins. Generation2, USER user, /home/user/app, platform-managed start/health commands; no Docker CMD/ENTRYPOINT.

## Problem solved

Provide concrete front-end scaffolds and persistent previews beyond generic Node execution, with reproducible installation and explicit resource ownership.

## Quick start (CLI)

Use the [native CLI setup](../docs/platform-steps.md) and paired credentials in process environment.

```bash
abx template deploy ./next-app -y --generation 2 \
  --start-cmd 'agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py' \
  --ready-cmd 'agent-sandbox-server healthcheck --port 9000'
abx create --template <template-id> -y
abx run <sandbox-id> scaffold --arg kind=next --arg path=preview-app
abx run <sandbox-id> dev_start --arg kind=next --arg path=preview-app
abx run <sandbox-id> dev_logs
abx run <sandbox-id> dev_stop
abx kill <sandbox-id> -y
abx template delete <template-id> -y
```

[Platform step preparation](../docs/platform-steps.md) is also supported structurally; a real provider receipt is still required. Standard-entry CLI syntax differs: inspect [entry compatibility](../docs/using-templates.md#client-entry-compatibility).

## Quick start (Python SDK)

Client distribution: `agent-sandbox-client`; import `agent_sandbox`. Install the [paired source client](../docs/python-client-installation.md).

```python
import asyncio
from urllib.parse import urlsplit
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=300)
    try:
        await sb.run("scaffold", kind="vite", path="preview-app")
        await sb.run("dev_start", kind="vite", path="preview-app",
                     allowed_host=urlsplit(sb.network.get_url(5173)).hostname)
        print(sb.network.get_url(5173))
        # Fetch/edit the preview before stopping it. Preserve desired source files.
        print(await sb.run("dev_logs", tail_bytes=4096))
        await sb.run("dev_stop")
    finally:
        await sb.kill()

asyncio.run(main())
```

SDK network.get_url supplies the provider's authoritative forwarded URL. Commands return ports; no host rewrite or invented CLI port command is needed. SDK files can edit app/page.js or index.html before fetching the preview again.

## Quick start (HTTP POST)

Use sb.network.get_url(9000) and set ABX_SERVER_URL to that URL. When configured, provide the command server token through process environment; see [prewarmed environment](../docs/runtime-environment.md).

```bash
curl --fail-with-body --request POST "$ABX_SERVER_URL/commands/scaffold" \
  --header 'Content-Type: application/json' \
  --header "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --data '{"kind":"next","path":"preview-app"}'
```

HTTP200 returns `{"result":{"path":"preview-app","kind":"next"}}`. POST /commands/dev_start with the same body, fetch the SDK3000 URL, then POST /commands/dev_stop with `{}`. Invalid schema400, unknown command404, runtime errors500. A client timeout does not cancel a server command.

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

Version1.1.0 adds allowed_host for Vite's exact SDK-forwarded hostname. The default empty value preserves localhost-only host authorization; pass urlsplit(sb.network.get_url(5173)).hostname from the SDK. It sets only the upstream-supported __VITE_ADDITIONAL_SERVER_ALLOWED_HOSTS, verified in pinned Vite8.3.4 source and [official server options](https://vite.dev/config/server-options#server-allowedhosts). Wildcards, leading-dot suffixes, schemes, ports, credentials, commas and empty DNS labels are refused. Next does not accept this Vite-only setting. Runtime1.0.0's actual forwarded Vite403 attempt remains a failure;the completed1.1.0 image/forwarded acceptance is linked below. No Host rewrite or global allow-all mode is used.

## Configuration

| Name | Default | Purpose |
|---|---|---|
| ABX_SERVER_TOKEN | empty | command-server Bearer authentication when set before startup |
| ABX_SERVER_PORT | 9000 | local server port |
| WORKSPACE | /home/user/app | existing workspace root |
| NEXT_APP_TOOLCHAIN | /opt/next-app | trusted pinned toolchain; local tests may select the installed source directory |

Development server environment contains only Node PATH, isolated temporary HOME, locale, telemetry opt-out and ownership marker. No cloud/model keys are inherited. The preview application itself has no password authentication; use provider access controls. Logs can include application output: do not publish raw log tails containing private data.

## Resources

2vCPU,2048MB; platform rootfs about10GiB; ports9000/3000/5173. No Docker/KVM/display required. Commands require Linux pidfds and procfs for identity-safe cleanup. Owner-marked detached workers and the unreaped process group are stopped; kernel listener absence is checked before cleanup succeeds.

## Verified


### Current image acceptance — 2026-10-22

| Provider | Current version and scope | Evidence |
| --- | --- | --- |
| alicloud-express | 1.1.0; regular image, actual CLI/SDK, complete HTTP 6 PASS / 0 FAIL / 0 SKIP, independent sandbox/template/private-registry cleanup | [Runtime and HTTP receipt](evidence/image-http-2026-10-20T102030Z.json) |
| opensandbox | 1.1.0; original Docker backend, every CLI/SDK named smoke, complete HTTP 6 PASS / 0 FAIL / 0 SKIP, independent SDK/container/process cleanup | [Native source image receipt](evidence/opensandbox-2026-10-22T112003Z.json) |

OpenSandbox CLI smoke uses actual `abx exec` into the guest named HTTP API. Generic `run_code` remains unsupported and `template launch` capability checks still apply. Missing model/vendor-account checks remain explicit skips in the receipts and do not establish model acceptance. [Reproduction and scope](../docs/source-image-acceptance.md).

<details>
<summary>Earlier acceptance records (original dates and scope retained)</summary>

Version1.1.0 passed actual SDK-created Express verified-image registration, native CLI/SDK self-test, full HTTP6 PASS/0 FAIL/0 SKIP and independent forwarded HTTP on3000/5173. Both real apps served SDK-written new source markers, then their owned workers/projects were stopped/deleted. Sandbox/template/registry cleanup and post-runtime digest independently confirmed. Vite uses only the exact SDK hostname. Default FC responses mark HTML as attachments; browser rendering and WebSocket/HMR are explicitly NOT_RUN, as are external providers.

| Version | Provider | Evidence |
| --- | --- | --- |
| 1.1.0 | alicloud-express | [SDK-created image](evidence/express-2026-10-20.json), [HTTP6](evidence/image-http-2026-10-20T102030Z.json), [independent forwarded source edits](evidence/forwarded-http-2026-10-20T102030Z.json) |

</details>

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
