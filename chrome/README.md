# chrome

[中文](README.zh-CN.md)

## What it does

Run original headed Chrome-for-Testing145.0.7632.6 on a private Xvfb/Openbox desktop, expose native CDP9222 and the unmodified Debian noVNC client6080, and retrieve real desktop PNGs. This is a browser application slice; no model, remote desktop product or benchmark score is claimed.

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a6`, installed directly by the Dockerfile.

Alibaba generation2 basev0.0.49/Python3.13/Linuxx64; original hash-checked Chrome ZIP; exact desktop/VNC Debian package pins; isolated hash-locked aiohttp3.14.5, pycryptodome4.1.0 and Pillow11.3.0. [Dockerfile](Dockerfile), [browser provenance](browser.json), [Python lock](requirements.lock), [design](../docs/design/chrome.md). Published server package.

## Problem solved

Use the same actual browser through automation and a visible interactive screen without nested Docker, KVM or a host browser. CDP9222 transparently forwards the native loopback9223 endpoint; noVNC6080 relays authenticated loopback5901 RFB. Browser processes run as user, with a private profile and Xauthority.

## Quick start (CLI)

CLI, SDK and HTTP are alternative ways to use the same application. Choose one for the task. Examples may write files, create projects or start services; do not repeat the full example on the same instance without cleaning its previous outputs.

Install the CLI/Python SDK and configure your platform with the [usage guide](../docs/using-templates.md#installation). The platform API key creates sandboxes; `ABX_SERVER_TOKEN` independently protects this template application. Run the following in your own terminal; cloning this repository is unnecessary.

These template commands require no model, model endpoint or model API key.

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ABX_HTTP_TIMEOUT=450
abx template launch Alibaba-Agent-Sandbox/awesome-templates//chrome --sandbox-timeout 1800 --yes
# Paste the sandbox ID from the launch output
export SANDBOX_ID='paste-id-from-launch-output'
abx sandbox command list "$SANDBOX_ID"
```

```bash
abx run "$SANDBOX_ID" chrome_start --json-args '{}'
abx run "$SANDBOX_ID" chrome_open --json-args '{"url":"https://example.com"}'
abx run "$SANDBOX_ID" chrome_screenshot --json-args '{}'
```

Returns the actual browser title and final URL. The following screenshot captures the same session.

`chrome_start` returns a session-specific VNC password. Resolve port 6080, open noVNC and log in with that password; CDP uses port 9222 and application authentication. Preserve provider URL paths, query strings and gateway headers unchanged. For direct CDP HTTP/WebSocket calls, add both `Authorization: Bearer <application-token>` and `X-Access-Token: <application-token>` after the gateway headers. The fallback is required when a provider proxy strips Authorization; an explicitly incorrect Authorization remains rejected. The noVNC connection still uses its original generated VNC password. Website accounts must be logged in within this remote session; local cookies are not imported.

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
            await client.commands.run('chrome_start')
            result = await client.commands.run('chrome_open', url='https://example.com')
            print(result)
            extra = await client.commands.run('chrome_screenshot')
            print(extra)
            Path("chrome.png").write_bytes(await sb.files.read_bytes(extra["path"]))
        finally:
            try:
                await client.commands.run('chrome_stop')
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

- `POST /commands/chrome_start` with `{}`.

`POST /commands/chrome_open`

```json
{
  "url": "https://example.com"
}
```

Use `Content-Type: application/json` and application authentication as described in the shared guide. The request body is the direct argument object, without an `args` wrapper. Success returns `{"result": ...}` with the value described above. Set the HTTP client wait to 450 seconds, separately from the command execution deadline. Responses are buffered, not event streams. Errors: 400 invalid arguments, 401 authentication, 404 unknown command, 500 execution failure.

After use, call:

- `POST /commands/chrome_stop` with `{}`.

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

The working directory is `/home/user/workspace`. Artifacts remain on the sandbox disk; export anything needed before deleting the instance. Delete only your own instance and the prepared template/image identified by its launch receipt.

```bash
# Download the path returned by chrome_screenshot
abx download "$SANDBOX_ID" '<returned-path>' ./chrome.png
abx run "$SANDBOX_ID" chrome_stop --json-args '{}'
abx kill "$SANDBOX_ID"
```

`abx kill` deletes the sandbox, not reusable prepared templates or images. Follow the [cleanup guide](../docs/using-templates.md#cli-sdk-and-http) for resources created by your launch.

## Resources

2 vCPU, 2048 MB, 1024×768 desktop. Ports: commands 9000, CDP 9222, noVNC 6080. One browser session per server; no GPU, KVM or nested Docker required. Chrome uses `--no-sandbox` within the outer sandbox rather than providing another isolation layer. Screenshots consume workspace storage.

## Contributing

To improve this template, see the [contribution guide](../CONTRIBUTING.md), [template specification](../docs/template-spec.md) and [design notes](../docs/design/chrome.md).

## Issues

CLI issues belong to [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Tracked by [Issue61](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/61). Report template/controller issues in this repository; client/server contract defects belong to [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues).

## License

Authored wrapper: Apache-2.0. Original Chrome-for-Testing and Debian components retain their respective licenses and notices. noVNC includes MPL2.0/BSD2/OFL1.1/CC-BY-SA3.0 and vendor licenses; this wrapper does not relicense those assets. See [UPSTREAM-NOTICE](UPSTREAM-NOTICE.md) and the installed native package copyright files.
