# chrome

[中文](README.zh-CN.md)

## What it does

Run original headed Chrome-for-Testing145.0.7632.6 on a private Xvfb/Openbox desktop, expose native CDP9222 and the unmodified Debian noVNC client6080, and retrieve real desktop PNGs. This is a browser application slice; no model, remote desktop product or benchmark score is claimed.

## Stack

Alibaba generation2 basev0.0.49/Python3.13/Linuxx64; original hash-checked Chrome ZIP; exact desktop/VNC Debian package pins; isolated hash-locked aiohttp3.14.5, pycryptodome4.1.0 and Pillow11.3.0. [Dockerfile](Dockerfile), [browser provenance](browser.json), [Python lock](requirements.lock), [design](../docs/design/chrome.md). Server source e2cb27e24fde0a67112f82b8d44af463445a5d1a.

## Problem solved

Use the same actual browser through automation and a visible interactive screen without nested Docker, KVM or a host browser. CDP9222 transparently forwards the native loopback9223 endpoint; noVNC6080 relays authenticated loopback5901 RFB. Browser processes run as user, with a private profile and Xauthority.

## Quick start (CLI)

Install the verified CLI0.4.1 native entry and configure authorized Express access as in [platform steps](../docs/platform-steps.md). Replace angle-bracket placeholders with unique owned values; publish the exact source commit before immutable COPY preparation. Wait for official READY before creation. The commands below open example.org and capture the actual desktop. CLI output from chrome_start contains the private temporary VNC password; keep it out of logs.

The `abx run` command uses the CLI0.4.1 native entry as `abx --native run`.

```bash
python scripts/prepare_steps.py chrome --output /tmp/chrome-steps-<unique-run> \
  --asset-transport parallel --server-commit e2cb27e24fde0a67112f82b8d44af463445a5d1a
abx --native template deploy /tmp/chrome-steps-<unique-run> --build steps -y
abx --native create --template <owned-template-id> -y
abx --native run <owned-sandbox-id> chrome_start
abx --native run <owned-sandbox-id> chrome_open --arg url=https://example.org
abx --native run <owned-sandbox-id> chrome_screenshot
abx --native run <owned-sandbox-id> chrome_stop
abx --native kill <owned-sandbox-id> -y
abx --native template delete <owned-template-id> -y
```

The canonical validation command is `ABX="abx --native" python scripts/run_steps_e2e.py chrome --sandbox-create sdk --http --asset-transport oss`. OSS uses a private exact-hash archive cache and independently verifies owned object/bucket cleanup. The source recipe remains authoritative; steps do not certify a Docker build.

## Quick start (Python SDK)

Install `agent-sandbox-client` through the [paired source instructions](../docs/python-client-installation.md). The example is syntax checked; actual acceptance uses an owned offline fixture as recorded below. It returns the same browser task as CLI/HTTP.

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<owned-template-id>", timeout=300)
    try:
        info = await sb.run("chrome_start", timeout=150)
        # Keep info["vnc_password"] private; enter it in the noVNC UI.
        cdp_url = sb.network.get_url(9222)
        vnc_url = sb.network.get_url(6080) + "/vnc.html"
        await sb.run("chrome_open", url="https://example.org", timeout=60)
        image = await sb.run("chrome_screenshot", timeout=60)
        png = await sb.files.read_bytes(image["path"], max_bytes=8 * 1024**2)
        assert png.startswith(b"\x89PNG\r\n\x1a\n")
        await sb.run("chrome_stop", timeout=90)
    finally:
        await sb.kill()

asyncio.run(main())
```

Use the selected provider gateway access headers for CDP and its WebSocket. Enter the generated password in noVNC; never add it to a URL. If the named server has ABX_SERVER_TOKEN, use `sb.server_at(9000, token=...)` and its commands client, closing that client in finally. The CDP relay also requires that Bearer token when configured. A client request timeout does not cancel the owned session; call chrome_stop or kill the disposable sandbox.

## Quick start (HTTP POST)

First call `POST /commands/chrome_start` with `{}`. Set ABX_SERVER_URL to `sb.network.get_url(9000)`; use the provider gateway header in addition to the independent server Bearer header when required.

```bash
curl --fail-with-body --request POST "$ABX_SERVER_URL/commands/chrome_open" \
  --header "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --header "Content-Type: application/json" --data '{"url":"https://example.org"}'
```

The body is the direct argument object, without an args wrapper. HTTP200 returns `{"result": {"url": "https://example.org/", "title": "Example Domain"}}` for the example. Follow with chrome_screenshot `{}` and chrome_stop `{}`. Missing/type-invalid arguments400, server auth401, unknown command404, semantic/execution errors500 with `{error,type}`. Browser/network failures retain their failure status.

## Command reference

| Command | Parameters / limits | Result / effects |
| --- | --- | --- |
| chrome_version | none | Actual browser_version145.0.7632.6 and native_binary_sha256; verifies fixed binary before execution |
| chrome_setup_check | none | installed/running/reserved_ports_available booleans, browser_version and mode; no launch |
| chrome_start | none | running, browser_version, cdp9222, vnc6080, vnc_path, private vnc_password, width1024, height768, headed, shm_bytes, optional cgroup limits, reused; creates desktop/profile/processes |
| chrome_status | none | Owned live status without password; stopped status includes owned_ports_absent/private_state_absent |
| chrome_open | url: required string, 1..2048 characters; HTTP(S) without whitespace/control/userinfo, or about:blank | Native final URL/title after navigation; existing session required |
| chrome_screenshot | none | Exclusive new workspace PNG: path/bytes/sha256/width/height; at most8MiB; retained for caller |
| chrome_stop | none | running:false, owned_ports_absent:true, private_state_absent:true only after owned cleanup |
| chrome_smoke | none | Exact manifest smoke string after actual CDP state, authenticated VNC/PNG and cleanup; rejects an active caller session |

Calls serialize. Startup readiness budget90seconds; navigation/CDP/VNC operations30seconds; use HTTP timeout150seconds for startup. Results are buffered. IPC messages are bounded8MiB and command inputs32KiB. Screenshot files use exclusive creation and mode0600. Stop preserves caller-owned screenshots and unrelated processes/files; the caller or sandbox deletion removes artifacts.

## Configuration

| Name | Default / requirement | Meaning |
| --- | --- | --- |
| WORKSPACE | /home/user/workspace; existing directory | Browser screenshot root, captured at command-module startup |
| ABX_SERVER_TOKEN | optional; empty | Named-server and CDP-relay Bearer authentication; separate from provider gateway/VNC auth |

[Runtime environment](../docs/runtime-environment.md) explains prewarmed processes: create-time env does not reconfigure an already-running server. Each owned session generates a private8-character VNC password and Xauthority cookie; password is returned only to the authorized start caller, never logged or passed in argv. Browser receives a minimal environment without operator cloud/model/GitHub credentials. Session HOME/profile/config/cookies/password files are private and removed on stop. A noVNC connection still needs the VNC password; protect forwarded URLs with provider access controls.

## Resources

Declared2vCPU/2048MB,1024×768 desktop, ports9000/9222/6080, internal9223/5901 and one owned X display. No Docker/KVM/GPU is required. Native Chrome uses --no-sandbox inside the disposable outer sandbox and --disable-dev-shm-usage; it is not an additional OS isolation boundary. Image rootfs guard8GiB. Actual Express /dev/shm was1031241728bytes; v2 cgroup memory/cpu paths were unavailable, so2CPU/2048MB is the declared template profile, not a measured peak or cgroup2limit. Separate actual L1 native image smoke measured64MiB shared memory; its CPU/memory were unrestricted. Rootfs measured1689714688bytes. These are distinct measurements, not a combined2GB/64MiB stress test. One session per server; generated downloads/screenshots consume caller workspace storage.

## Verified

| Provider | Date | Scope | Evidence |
| --- | --- | --- | --- |
| alicloud-express | 2026-10-20 |1.0.5; original native headed Chrome145, SDK-created canonical steps, CLI/SDK smoke, fullHTTP30/0/0, independent owned cleanup | [Receipt](evidence/express-2026-10-20T230349Z.json), [controller/provenance](evidence/verification-steps-2026-10-20T230349Z.json) |

Exact runtime/controller source cd144246bcd3e2ba37865d90e24cba612db8b11b; actual [L1 native image smoke](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/39512397976) also passed, separately measuring64MiB shared memory. Original native CDP/noVNC/RFB authentication, actual VNC pointer input with independent DOM/redraw, valid named navigation with external CDP readback, independently downloaded PNG/bytes/hash/regions/fresh ACK and owned native/private/display/listener/sandbox/template/OSS absence all passed. Duration156.468seconds. No model/benchmark/other-provider claim. [Final record](../.agents/evidence/verify/2026-10-20-chrome-native-final.md). Historical white-cursor sampling failures and diagnostic-only attempts remain unchanged; local/source-only checks do not grant provider qualification.

## Secondary development

Change browser.json, installer fixed digest/version, native provenance checks, system dependency pins and smoke assertions together. Preserve original browser notices. Revalidate genuine native CDP and password-authenticated RFB, including an actual VNC pointer click and independent CDP state assertion. Do not substitute a screenshot fixture or HTTP echo for the native browser.

## Contributing

Follow [CONTRIBUTING](../CONTRIBUTING.md), [project standards](../docs/project-standards.md) and [documentation standards](../docs/documentation-standards.md). Keep both README languages, design, catalog and dated receipts consistent.

## Issues

CLI issues belong to [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Tracked by [Issue61](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/61). Report template/controller issues in this repository; client/server contract defects belong to [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues).

## License

Authored wrapper: Apache-2.0. Original Chrome-for-Testing and Debian components retain their respective licenses and notices. noVNC includes MPL2.0/BSD2/OFL1.1/CC-BY-SA3.0 and vendor licenses; this wrapper does not relicense those assets. See [UPSTREAM-NOTICE](UPSTREAM-NOTICE.md) and the installed native package copyright files.
