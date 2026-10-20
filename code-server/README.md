# code-server

## What it does

Runs the pinned code-server browser IDE with mandatory password authentication, owned start/status/stop and isolated configuration, user data and extensions. Caller IDE settings stay intact.

## Stack

Alibaba FC base v0.0.49; official code-server4.141.0 standalone Linux x86_64/aarch64 assets with bundled upstream Node/VS Code runtime. [assets.json](assets.json) fixes URLs, byte lengths and official SHA256. Bundled license notices are preserved. Server SDK is pinned to e2cb27e; generation2/non-root user.

## Problem solved

A real browser IDE for editing sandbox workspaces without local Docker, KVM, desktop display or a model key.

## Quick start (CLI)

Native CLI syntax; see [entry compatibility](../docs/using-templates.md#client-entry-compatibility). Use the SDK to read a private password from your process environment.

```bash
abx template deploy ./code-server -y
abx create --template <template-id> --timeout 300 -y
abx run <sandbox-id> code_server_version
abx run <sandbox-id> code_server_self_test
abx run <sandbox-id> code_server_start --arg 'password=<your-private-12-byte-or-longer-password>'
abx run <sandbox-id> code_server_status
abx run <sandbox-id> code_server_stop
abx kill <sandbox-id> -y
abx template delete <template-id> -y
```

## Quick start (Python SDK)

Install the [paired `agent-sandbox-client`](../docs/python-client-installation.md):

```python
import asyncio
import os
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=300)
    try:
        await sb.run("code_server_start", password=os.environ["CODE_SERVER_PASSWORD"])
        print(sb.network.get_url(8443))
        # Open this URL in your browser and log in with the same private password.
        # Export any workspace files you need before destroying the sandbox.
        await asyncio.to_thread(input, "Press Enter when finished editing: ")
        await sb.run("code_server_stop")
    finally:
        await sb.kill()
        await sb.close()

asyncio.run(main())
```

## Quick start (HTTP POST)

```bash
curl -fsS -X POST -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <server-token>' -d '{}' \
  '<sandbox-port-9000-url>/commands/code_server_self_test'
```

Response: `{"result":"CODE_SERVER_OK"}`. The IDE is a separate password-protected HTTP/WebSocket service on8443.

## Command reference

| Command | Parameters | Result |
| --- | --- | --- |
| code_server_version | none | actual installed version string |
| code_server_start | password: str optional empty=server CODE_SERVER_PASSWORD; port: int=8443,1024..65535 excluding9000; cwd: str empty=WORKSPACE,existing workspace directory; timeout_s: int=60,1..120 | {port,running:true,auth:password} after actual health |
| code_server_status | none | {running:false}, or {running:true,port,auth:password} |
| code_server_stop | none | {running:false} only after owned processes exit, kernel listener absence and private-state cleanup |
| code_server_self_test | none; existing owned IDE must be stopped | CODE_SERVER_OK after real password rejection/login/workbench and cleanup |

Passwords require12..256 UTF-8 bytes without NUL. Occupied ports and duplicate starts fail before launch. Stop never kills a process by generic name. Failed startup/cleanup does not report success. An inherited random owner marker and Linux pidfds pin owned upstream workers before signaling; kernel listener absence is independently checked.

## Configuration

For an operator-local SDK preview that preserves upstream TLS, see the [local preview operation](../docs/preview-proxy.md). Direct-domain and sdk-local controller results are recorded separately.


WORKSPACE defaults to /home/user/app. CODE_SERVER_PASSWORD and ABX_SERVER_TOKEN are empty manifest placeholders. The former can be supplied per call; the latter protects the9000 command API and does not replace IDE authentication on8443. See [prewarmed environment](../docs/runtime-environment.md). Private directories/config are0700/0600. Cloud/model keys are not inherited by the IDE. Update checks and telemetry are disabled.

## Resources

2vCPU/2048MB; command API9000 and IDE8443. Other port choices require separate provider forwarding. Image build enforces at most8GiB visible rootfs with du -sx; download budget240seconds and exact asset lengths. Startup is bounded to120seconds, inspection/child output are bounded. Stop removes this IDE instance's config/user data/extensions; workspace files remain.

## Verified

| Version | Provider | Mode and scope | Evidence |
| --- | --- | --- | --- |
| 1.0.0 | alicloud-express | SDK-created verified image; full HTTP5; actual browser/terminal/editor through sdk-local preview | [image](evidence/express-2026-10-20.json), [HTTP](evidence/image-http-2026-10-20T091440Z.json), [browser](evidence/browser-ui-2026-10-20T091440Z.json) |

Actual Chromium loaded the native JavaScript workbench, wrote a nonce through the terminal WebSocket, edited/saved it with Monaco and independently confirmed bytes through the SDK. Upstream HTTPS certificate/hostname verification stayed enabled; the local browser used HTTP loopback. The relay exchanged its capability before real IDE password login. Browser/proxy/IDE/nonce cleanup and sandbox/template/registry absence were independently confirmed. Use the [SDK local preview operation](../docs/preview-proxy.md); default FC direct mode still forces HTML attachment and its earlier failures remain historical. This does not certify direct-domain browser rendering or other providers.

### Actual browser, terminal and editor check

Install Playwright1.58.0, its Chromium browser and `certutil` (Debian/Ubuntu:
`libnss3-tools`). With an exclusively caller-owned sandbox and no running IDE,
execute `python code-server/browser_e2e_test.py --sandbox-id <sandbox-id>`.
It logs in through the SDK-forwarded8443 URL, loads workbench JavaScript, writes
a nonce through the terminal WebSocket, independently reads it through files SDK,
edits/saves in the browser and independently reads the changed bytes. It stops
its IDE and removes its nonce file; the caller must destroy the sandbox.

TLS stays enabled. Chromium uses a private temporary HOME/NSS store containing
only CA certificates already trusted by Python's default SSL context from the
operator's configured bundles. It preserves the caller's browser profile and
filters cloud/model credentials from browser children. For a private network CA,
configure the operator trusted store first. No certificate validation bypass is
used. Local browser regressions explicitly use a filesystem observer and do not
establish cloud/SDK acceptance. Cleanup failure prevents a passing result.

### Default-domain browser prerequisite

A real minimal HTML service on the currently configured default FC domain returned
HTTP200/text-html with forced `Content-Disposition: attachment`; actual Chromium
started a download. TLS verification remained enabled. The independent probe and
sandbox absence readback are in [the complete control](evidence/preview-header-control-2026-10-20T060339Z.json).
This matches the [official default-domain restriction](https://www.alibabacloud.com/help/en/functioncompute/web-functions).

Bind a provider-supported custom preview domain with a valid certificate and
configure the SDK to use the provider-returned domain before browser UI use.
Changing a hostname string alone does not register a mapping. Run the browser
controller again against that SDK URL. It now diagnoses forced HTML attachment
before browser startup and still cleans up its IDE. The existing CLI/SDK examples
need that access prerequisite for interactive browser use.

The [actual image attempt](evidence/image-attempt-2026-10-20T055537Z.json) passed
complete HTTP5 checks but [failed real browser UI](evidence/browser-ui-2026-10-20T055537Z.json).
Owned sandbox/template and registry cleanup were independently confirmed. It is
not qualified as a complete browser IDE deployment; Issue53 remains open.

## Secondary development

For local tools use install_runtime.py --prefix in your own directory. Image builds explicitly enable --check-rootfs; Docker host statvfs usage is not image size. Prepare [platform steps](../docs/platform-steps.md): `python scripts/prepare_steps.py code-server --output /tmp/ide-steps`; actual acceptance: `python scripts/run_steps_e2e.py code-server`. Update asset/version assertions and both docs together. WebSocket/terminal interaction needs its own recorded test; authenticated HTML alone does not certify it.

## Contributing

Follow [CONTRIBUTING.md](../CONTRIBUTING.md), [spec](../docs/template-spec.md) and [design](../docs/design/code-server.md). Test real authentication, wrong passwords, cross-request state and kernel/process readback. A successful TCP connect to an empty proxied port is not a listener proof.

## Issues

[Issue53](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/53); CLI: [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues); SDK: [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues).

## License

Template: Apache-2.0; code-server: MIT. Preserve official bundled LICENSE/third-party notices, including VS Code/Node components. User-installed extensions retain their own licenses. [Upstream release](https://github.com/coder/code-server/releases/tag/v4.141.0).

### Additional current-version platform-step acceptance

[Actual steps](evidence/express-2026-10-20T135352Z.json) and [external HTTP attempt](evidence/verification-steps-2026-10-20T135352Z.json): official READY, Python SDK creation, CLI/SDK smoke and 5 HTTP PASS / 0 FAIL / 0 SKIP. Model calls remain NOT_RUN in this receipt. Independent sandbox/template and private same-account asset-cache object/bucket cleanup passed before publication. Earlier image/model receipts retain their own scope.
