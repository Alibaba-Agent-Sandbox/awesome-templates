# chrome

[中文](README.zh-CN.md)

## What it does

Run original headed Chrome-for-Testing145.0.7632.6 on a private Xvfb/Openbox desktop, expose native CDP9222 and the unmodified Debian noVNC client6080, and retrieve real desktop PNGs. This is a browser application slice; no model, remote desktop product or benchmark score is claimed.

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a4`, installed directly by the Dockerfile.

Alibaba generation2 basev0.0.49/Python3.13/Linuxx64; original hash-checked Chrome ZIP; exact desktop/VNC Debian package pins; isolated hash-locked aiohttp3.14.5, pycryptodome4.1.0 and Pillow11.3.0. [Dockerfile](Dockerfile), [browser provenance](browser.json), [Python lock](requirements.lock), [design](../docs/design/chrome.md). Published server package.

## Problem solved

Use the same actual browser through automation and a visible interactive screen without nested Docker, KVM or a host browser. CDP9222 transparently forwards the native loopback9223 endpoint; noVNC6080 relays authenticated loopback5901 RFB. Browser processes run as user, with a private profile and Xauthority.

## Quick start (CLI)

Follow the [usage guide](../docs/using-templates.md#installation) to install the clients, configure the provider and set an independent `ABX_SERVER_TOKEN`. From this repository's root, launch the application and retain its sandbox ID. Replace `<sandbox-id>` below with that ID.

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./chrome --yes
abx run <sandbox-id> chrome_smoke --json-args '{}'
```

`template launch` prepares and starts this instance's application. For OpenSandbox, set `ABX_PROVIDER=opensandbox` above and use `provider="opensandbox"` in Python. See the [complete calling flow](../docs/using-templates.md#cli-sdk-and-http) for OpenSandbox configuration, provider selection on every call and owned-resource cleanup. The next examples reuse the same running instance.

## Quick start (Python SDK)

Install `agent-sandbox-client` and follow the [Python connection example](../docs/using-templates.md#cli-sdk-and-http), using `ProviderSandbox.connect` and `application_client` with the independent application token. Replace the command call inside that example's `try` block with:

```python
print(await client.commands.run('chrome_smoke'))
```

Keep the guide's connection and close steps. `sb.commands.run` executes a process; `client.commands.run` calls this template's named commands. Business commands, arguments and limits are listed in the command reference below.

## Quick start (HTTP POST)

Follow the [HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserve gateway headers, path and query parameters, and set the independent application token. Change the request to `POST /commands/chrome_smoke`, with `Content-Type: application/json` and this direct argument object:

```json
{}
```

Expected response for this check:

```json
{"result": "native headed Chrome145.0.7632.6 CDP/VNC/PNG and cleanup OK"}
```

`result` is buffered, not an event stream. Missing or mistyped arguments return 400, failed authentication 401, unknown commands 404, and execution errors 500. Set the HTTP wait and command deadline separately; a client timeout does not guarantee cancellation.

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
| ABX_SERVER_TOKEN | required; empty declaration | Export an independent application token before launching the template; separate from model and gateway credentials. Also used for CDP relay authentication. |

[Runtime environment](../docs/runtime-environment.md) explains prewarmed processes: create-time env does not reconfigure an already-running server. Each owned session generates a private8-character VNC password and Xauthority cookie; password is returned only to the authorized start caller, never logged or passed in argv. Browser receives a minimal environment without operator cloud/model/GitHub credentials. Session HOME/profile/config/cookies/password files are private and removed on stop. A noVNC connection still needs the VNC password; protect forwarded URLs with provider access controls.

## Resources

Declared2vCPU/2048MB,1024×768 desktop, ports9000/9222/6080, internal9223/5901 and one owned X display. No Docker/KVM/GPU is required. Native Chrome uses --no-sandbox inside the disposable outer sandbox and --disable-dev-shm-usage; it is not an additional OS isolation boundary. Image rootfs guard8GiB. Actual Express /dev/shm was1031241728bytes; v2 cgroup memory/cpu paths were unavailable, so2CPU/2048MB is the declared template profile, not a measured peak or cgroup2limit. Separate actual L1 native image smoke measured64MiB shared memory; its CPU/memory were unrestricted. Rootfs measured1689714688bytes. These are distinct measurements, not a combined2GB/64MiB stress test. One session per server; generated downloads/screenshots consume caller workspace storage.

## Verified

Version 1.0.6 retains provider-resolved URL paths and query parameters for CDP and noVNC connections. Pass each endpoint returned by the provider unchanged; do not replace it with the native browser host.

See [test results and scope](../docs/using-templates.md#evidence-and-providers). The dated records below identify the tested input and entry point.

## Secondary development

Change browser.json, installer fixed digest/version, native provenance checks, system dependency pins and smoke assertions together. Preserve original browser notices. Revalidate genuine native CDP and password-authenticated RFB, including an actual VNC pointer click and independent CDP state assertion. Do not substitute a screenshot fixture or HTTP echo for the native browser.

## Contributing

Follow [CONTRIBUTING](../CONTRIBUTING.md), [project standards](../docs/project-standards.md) and [documentation standards](../docs/documentation-standards.md). Keep both README languages, design, catalog and dated receipts consistent.

## Issues

CLI issues belong to [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Tracked by [Issue61](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/61). Report template/controller issues in this repository; client/server contract defects belong to [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues).

## License

Authored wrapper: Apache-2.0. Original Chrome-for-Testing and Debian components retain their respective licenses and notices. noVNC includes MPL2.0/BSD2/OFL1.1/CC-BY-SA3.0 and vendor licenses; this wrapper does not relicense those assets. See [UPSTREAM-NOTICE](UPSTREAM-NOTICE.md) and the installed native package copyright files.
