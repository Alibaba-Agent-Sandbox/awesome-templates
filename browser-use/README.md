# Browser-use

[中文](README.zh-CN.md)

## What it does

Runs the actual browser-use0.13.11 agent on a private local Chromium browser. It reads text DOM, performs browser interactions and returns a real PNG plus final URL/result. This complements model-free Playwright primitives; it does not use Browser Use Cloud or a remote browser.

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a6`, installed directly by the Dockerfile.

FC base v0.0.49/generation2/non-root Linux x86_64/Python3.13. [requirements.lock](requirements.lock) pins browser-use0.13.11 and every transitive version/SHA256; [requirements.in](requirements.in) is compiled by uv0.11.28. The package uses CDP-use, not a Python Playwright dependency. An explicitly pinned Playwright1.58.0 installer selects Chromium1208/Google Chrome for Testing145.0.7632.6; --no-shell avoids another headless-shell copy.

## Problem solved

Give a real model a local browser inside an owned sandbox, with independent artifact retrieval and process cleanup. Text-DOM use_vision=false needs no vision-capable model. Cloud browser billing/accounts, browser extensions and arbitrary local files/shell are outside this profile.

## Quick start (CLI)

CLI, SDK and HTTP are alternative ways to use the same application. Choose one for the task. Examples may write files, create projects or start services; do not repeat the full example on the same instance without cleaning its previous outputs.

Install the CLI/Python SDK and configure your platform with the [usage guide](../docs/using-templates.md#installation). The platform API key creates sandboxes; `ABX_SERVER_TOKEN` independently protects this template application. Run the following in your own terminal; cloning this repository is unnecessary.

Fill in model settings before launch: the API key, endpoint and model ID must belong to the same model service and region. `https://model.example.invalid/v1` is a placeholder; replace it with your vendor API base, not a web chat URL. Use a model ID actually available at that endpoint.

This entry uses a model API key: no browser OAuth login is required, and your local logged-in account is not imported. See Configuration for protocol requirements. This template uses **Chat Completions**; an “OpenAI-compatible” label alone does not establish support for that API.

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export BROWSER_USE_API_KEY='<your-model-api-key>'
export BROWSER_USE_BASE_URL='https://model.example.invalid/v1'
export BROWSER_USE_MODEL='<your-model-id>'
export ABX_HTTP_TIMEOUT=450
abx template launch Alibaba-Agent-Sandbox/awesome-templates//browser-use --sandbox-timeout 1800 --yes
# Paste the sandbox ID from the launch output
export SANDBOX_ID='paste-id-from-launch-output'
abx sandbox command list "$SANDBOX_ID"
```

```bash
abx run "$SANDBOX_ID" browser_use --json-args '{"task":"Read the heading of this page and return it.","url":"https://example.com","max_steps":8,"command_timeout":300}'
```

Returns the agent result, `done`, `success` and a fresh `screenshot_path`. Inspect completion flags; text alone is not a success indicator.

The browser uses a fresh private in-sandbox profile, without local login state or cookies. Handle website login within the relevant remote browser session. browser-use/Stagehand remove private sessions after each call; they do not promise persistent account sessions. The public-page example requires outbound network access.

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
            result = await client.commands.run('browser_use', task='Read the heading of this page and return it.', url='https://example.com', max_steps=8, command_timeout=300)
            print(result)
            Path('browser-use.png').write_bytes(await sb.files.read_bytes(result['screenshot_path']))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

The SDK returns the command value; it unwraps the HTTP `result` envelope. Closing the client does not delete the sandbox.

## Quick start (HTTP POST)

Resolve port 9000 on the same instance with the [HTTP calling example](../docs/using-templates.md#cli-sdk-and-http). Preserve gateway headers, URL path and query before adding the independent application authentication.

`POST /commands/browser_use`

```json
{
  "task": "Read the heading of this page and return it.",
  "url": "https://example.com",
  "max_steps": 8,
  "command_timeout": 300
}
```

Use `Content-Type: application/json` and application authentication as described in the shared guide. The request body is the direct argument object, without an `args` wrapper. Success returns `{"result": ...}` with the value described above. Set the HTTP client wait to 450 seconds, separately from the command execution deadline. Responses are buffered, not event streams. Errors: 400 invalid arguments, 401 authentication, 404 unknown command, 500 execution failure.

## Command reference

| Command | Parameters | Result |
| --- | --- | --- |
| browser_use_version | none | actual installed0.13.11 string |
| browser_use_setup_check | none | installed/version/browser_installed and api_key_set/base_url_set/model_set flags |
| browser_use_self_test | none | BROWSER_USE_NATIVE_OK only after native CDP navigation/title/PNG and cleanup; no model |
| browser_use | task:str required, nonempty/no NUL/max256KiB UTF-8; url:str="", HTTP(S)/no userinfo/max8192 UTF-8 bytes; max_steps:int=8,1..20; command_timeout:int=300,1..900seconds | {result:str,final_url:str,screenshot_path:str,bytes:int,steps:int,done:bool,success:bool} |

The native worker uses explicit Agent/BrowserSession/BrowserProfile/ChatOpenAI, no automatic cloud selection. Compatible text JSON is parsed by native browser-use; add_schema_to_system_prompt=true and dont_force_structured_output=true avoid requiring a provider-specific strict response-format API.

Exactly15 native actions are enabled: done/navigate/click/input/scroll/wait/go_back/switch/close/find_text/find_elements/search_page/select_dropdown/dropdown_options/send_keys. The registry is checked before and after Agent construction. Filesystem/shell/evaluate/extract/upload/PDF/search and screenshot-as-agent-action are excluded. The wrapper takes its own actual screenshot at completion. New random artifact names are never caller-specified or overwritten. PNG16MiB is a post-render limit. The URL is read from the actual current target; a model statement alone is not verification.

## Configuration

This entry calls compatible Chat Completions. Include the vendor API prefix (often `/v1`) in the base; do not append `/chat/completions`. This entry uses text DOM and requires structured JSON according to the native prompt. It does not use a Browser Use Cloud account.

| Name | Required | Default | Purpose |
| --- | --- | --- | --- |
| BROWSER_USE_API_KEY | model turns | empty | explicitly supplied compatible-model credential, not Browser Use Cloud |
| BROWSER_USE_BASE_URL | model turns | empty | HTTP(S) model API; no userinfo/query/fragment |
| BROWSER_USE_MODEL | model turns | empty | explicit compatible chat model ID |
| BROWSER_USE_PYTHON | no | /opt/browser-use/bin/python | hash-locked native environment; actual0.13.11 checked |
| PLAYWRIGHT_BROWSERS_PATH | no | /opt/playwright | installed Chromium1208 cache |
| BROWSER_USE_BROWSER_BINARY | diagnostics | Chromium1208/chrome-linux64/chrome | executable override; actual145.0.7632.6 still required |
| WORKSPACE | no | /home/user/app | owned root for new browser-use-artifacts PNGs |
| ABX_SERVER_TOKEN | yes | empty | Export an independent application token before the template launch; separate from model and gateway credentials |

Model settings enter private file stdin only; they are not inherited into Chromium. Every call has fresh HOME/XDG/profile/native file-system state. Disable native telemetry/cloud sync/default extensions and use_cloud; no caller profile or saved browser account is imported. CDP launch requests loopback binding and only command9000 is advertised. This container-only profile explicitly sets chromium_sandbox=false instead of relying on Docker detection; the owned sandbox supplies OS isolation. The browser and model still have sandbox-user authority and network access; these action restrictions are not another OS isolation boundary. Returned result/PNG can contain private webpage information; exact configured model key/base values are redacted from result strings.

The working directory is `/home/user/app`. Artifacts remain on the sandbox disk; export anything needed before deleting the instance. Delete only your own instance and the prepared template/image identified by its launch receipt.

```bash
# Replace <returned-path> with screenshot_path from the result
abx download "$SANDBOX_ID" '<returned-path>' ./browser-use.png
abx kill "$SANDBOX_ID"
```

`abx kill` deletes the sandbox, not reusable prepared templates or images. Follow the [cleanup guide](../docs/using-templates.md#cli-sdk-and-http) for resources created by your launch.

## Resources

2vCPU/2048MB, named-command port9000. --disable-dev-shm-usage avoids relying on a large /dev/shm. One browser operation per server; concurrent heavy calls fail busy500. max_steps1..20; max3 actions/step; model90seconds/0retry/4096tokens; native action30/step120/LLM100second guards; outer command1..900seconds plus bounded cleanup. Each captured stream256KiB. Private browser/config/files/processes removed on ordinary success/failure/deadline; the PNG remains caller-owned. Sandbox deletion is the final boundary after abrupt server loss or hostile same-user code. Image rootfs has an8GiB build gate.

## Contributing

To improve this template, see the [contribution guide](../CONTRIBUTING.md), [template specification](../docs/template-spec.md) and [design notes](../docs/design/browser-use.md).

## Issues

[Issue51](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/51); templates/catalog [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues), client/server [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), CLI [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).

## License

Wrapper code is [Apache-2.0](../LICENSE). Browser-use is MIT; preserve the [unchanged upstream license](upstream-LICENSE). The unmodified Playwright-distributed Chrome for Testing build retains its bundled license/notices; Playwright is Apache-2.0. Every hash-locked dependency keeps its installed upstream notices; do not relabel the full image as Apache-2.0. No model weights or cloud service account is included.

Failed native steps include at most20 error summaries, each truncated to1024 UTF-8 bytes after exact configured model-key/endpoint redaction.


## Verification entry points

Required-use controller: `E2E_REQUIRE_LLM=1` exercises the configured public application against an owned nonce browser fixture, then independently checks actual page state and downloaded PNG. It does not start another command server or copy model keys into the host controller. Native SDK model controllers remain available as separate borrowed-sandbox checks.
