# browser-automation

[中文](README.zh-CN.md)

## What it does

Python browse/scrape/fill_form requests each own a separate browser. Native MCP calls deliberately share one owned browser session until stop or idle close; mcp_stop removes its private profile/output.

Navigate with headless Chromium, save PNG screenshots, extract text and links,
and fill forms. Each named command owns and closes a fresh browser; concurrent
requests do not share cookies, DOM state, or form values. Form filling verifies
input values internally and returns only a count. It does not submit the form.

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a6`, installed directly by the Dockerfile.

Alibaba runtime base (default `v0.0.49`, Python 3.13); Playwright `1.58.0` with
its matching Chromium revision; pinned `agent-sandbox-server` archive in the
Dockerfile. Browser launches use `--disable-dev-shm-usage` for the Express 64 MB
shared-memory limit. This template exposes named commands, files and process
APIs; optional built-in `/browser/*` endpoints are not enabled.

## Problem solved

Give an agent reproducible browser operations and downloadable artifacts without
requiring Docker, KVM, a desktop, a model API key, or a persistent browser session.

## Quick start (CLI)

CLI, SDK and HTTP are alternative ways to use the same application. Choose one for the task. Examples may write files, create projects or start services; do not repeat the full example on the same instance without cleaning its previous outputs.

Install the CLI/Python SDK and configure your platform with the [usage guide](../docs/using-templates.md#installation). The platform API key creates sandboxes; `ABX_SERVER_TOKEN` independently protects this template application. Run the following in your own terminal; cloning this repository is unnecessary.

These template commands require no model, model endpoint or model API key.

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ABX_HTTP_TIMEOUT=450
abx template launch Alibaba-Agent-Sandbox/awesome-templates//browser-automation --sandbox-timeout 1800 --yes
# Paste the sandbox ID from the launch output
export SANDBOX_ID='paste-id-from-launch-output'
abx sandbox command list "$SANDBOX_ID"
```

```bash
abx run "$SANDBOX_ID" browse --json-args '{"url":"data:text/html,<title>Invoice</title><h1>Total: 51.30</h1>","action":"extract"}'
```

Returns `action: extract`, `title: Invoice` and visible text containing `Total: 51.30`.

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
            result = await client.commands.run('browse', url='data:text/html,<title>Invoice</title><h1>Total: 51.30</h1>', action='extract')
            print(result)
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

The SDK returns the command value; it unwraps the HTTP `result` envelope. Closing the client does not delete the sandbox.

## Quick start (HTTP POST)

Resolve port 9000 on the same instance with the [HTTP calling example](../docs/using-templates.md#cli-sdk-and-http). Preserve gateway headers, URL path and query before adding the independent application authentication.

`POST /commands/browse`

```json
{
  "url": "data:text/html,<title>Invoice</title><h1>Total: 51.30</h1>",
  "action": "extract"
}
```

Use `Content-Type: application/json` and application authentication as described in the shared guide. The request body is the direct argument object, without an `args` wrapper. Success returns `{"result": ...}` with the value described above. Set the HTTP client wait to 450 seconds, separately from the command execution deadline. Responses are buffered, not event streams. Errors: 400 invalid arguments, 401 authentication, 404 unknown command, 500 execution failure.

## Command reference

All commands use `POST /commands/<name>` and return `{"result": ...}`.
All results are buffered, not streaming.

| Command | Parameters (type; required/default; range) | Result |
|---|---|---|
| `browse` | `url`: string, required; `action`: string=`screenshot`, one of `screenshot`, `extract`, `links`, `full`; `timeout_s`: integer=30, 1–120 | Always `action`, `title`; screenshot adds absolute PNG `path`; extract adds `text`; links adds `count`, `links:[{href,text}]`; full adds `screenshot`, `text_preview` (first 500 characters) |
| `scrape` | `url`: string, required; `selector`: nonempty CSS string, required; `timeout_s`: integer=30, 1–120 | `{count,texts:[string]}`; no matches returns count 0 |
| `fill_form` | `url`: string, required; `fields_json`: string, required, JSON array of 1–100 `{selector: nonempty string,value: string}` objects with no other keys; `timeout_s`: integer=30, 1–120 | `{fields_filled:integer}`; never echoes values, selectors, URL, title or DOM |
| `run` | `script`: string=`main.py`, existing workspace Python file (resolved symlinks must stay in the workspace); `timeout_s`: integer=120, 1–120, subprocess deadline | Successful stdout string; nonzero exit/timeout fails without returning captured output |

Browser URLs accept `http`, `https`, and inline `data:text/html,` pages. Embedded
URL username/password and `file:` URLs are rejected. Redirects and subresources
are browser-controlled; the template is not a network allowlist. `fill_form`
uses Playwright `locator.fill` and checks `input_value`; it supports text-like
inputs and textareas, not checkbox/select/submit actions.

Example form argument (synthetic values only):

```json
{"url":"https://example.com/login","fields_json":"[{\"selector\":\"#email\",\"value\":\"sample@example.invalid\"}]"}
```

### Native Playwright MCP

The image includes official `@playwright/mcp@0.0.83`, lockfile-pinned JavaScript Playwright1.64.0-alpha-1790635538000 and reuses the existing Chromium1208. No second Chromium or model credential is installed. The Python browser API remains pinned1.58.0.

| Command | Parameters | Result |
| --- | --- | --- |
| mcp_start | none | running, port8931, mcp_version and negotiated protocol_version |
| mcp_status | none | running:false or current owned MCP status |
| mcp_call | method:str required, tools/list or tools/call or ping; params_json:str="{}", JSON object up to64KiB | actual MCP result object; inspect isError for tool failures |
| mcp_stop | none | running:false after owned process/browser/listener cleanup |
| mcp_self_test | none | PLAYWRIGHT_MCP_OK only after actual initialization/tools, two browser clicks independently observed by an owned HTTP fixture, real PNG screenshot and cleanup |

Run `abx run <sandbox-id> mcp_start`, then `abx run <sandbox-id> mcp_call --arg method=tools/list`. Inside that same sandbox a standard MCP client uses `http://127.0.0.1:8931/mcp` with the native MCP HTTP session/protocol headers. The listener is private to the sandbox;8931 is not an authenticated public gateway. Outside clients use SDK `await client.commands.run("mcp_call", method="tools/list")` through the command server's configured bearer authentication. For browser_click, the pinned upstream schema uses `target` from a fresh browser_snapshot; it does not use the old ref argument.

A process-start diagnostic `MCP_NODE_MODULES` may select an independently installed exact lockfile tree; production uses /opt/playwright-mcp/node_modules. MCP HOME/profile/output are private and deleted on stop; no saved browser/profile/extensions are loaded. Default action/navigation limits10/20seconds, HTTP response4MiB, native output-file eviction threshold10MiB (not a hard disk quota) and idle browser60seconds. Calls are serialized; streaming stays on the native in-sandbox MCP endpoint, while mcp_call returns a buffered result. Native child environment excludes operator cloud/model/server keys and Node injection variables. Browser navigation shares the sandbox's egress authority; no SSRF policy is added. Caller requests, page data and results can be private and must not be publicly logged.

### PDF and bounded workspace scripts

`pdf(url:str, landscape:bool=false, print_background:bool=true, timeout_s:int=30) -> {path,bytes,format:"PDF"}` renders A4 using the pinned real Chromium. URL supports the same schemes as browse, up to256KiB/no NUL. The generated workspace PDF is capped at16MiB after rendering; this is not a peak-memory bound. Boolean flags are typed. Read the artifact with SDK `await sb.files.read_bytes(result["path"])` and remove it after export. `abx run <sandbox-id> pdf --arg url='data:text/html,<h1>PDF proof</h1>'` exercises the actual renderer. No caller output filename is overwritten; symlink artifact directories are refused.

PDF execution runs in a private-HOME child with its own1–120second execution deadline and bounded teardown. Generic run now also reserves process identity and stops marked detached/ordinary children on success, failure, overflow or deadline. stdout/stderr are each capped at256KiB; native diagnostics are omitted from errors. run preserves caller HOME but forwards only PATH/locale/browser/CA settings, excluding server/cloud/model keys and injected loaders. Use the SDK process interface for explicit long-lived background work/environment settings. This process hygiene is not a second sandbox security boundary. Build enforces actual du rootfs accounting at8GiB; disk free-space size is a separate quantity.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `PLAYWRIGHT_BROWSERS_PATH` | `/opt/playwright` in the image | Shared readable Chromium installation |
| `WORKSPACE` | `/home/user/app` | Script root and `browser-artifacts/` output root; keep aligned with the server file policy |
| `ABX_SERVER_TOKEN` | empty | Export an independent application token before the template launch; separate from model and gateway credentials |
| `ABX_SERVER_PORT` | `9000` | Local `python3 commands.py` server port |

Outputs from extraction, screenshots, links and user scripts may contain sensitive
page content. Treat artifacts as private; do not print them into shared logs.
Never bake credentials into images or YAML. Form errors and success responses do
not echo entered values. User scripts are responsible for their own stdout.

The working directory is `/home/user/app`. Artifacts remain on the sandbox disk; export anything needed before deleting the instance. Delete only your own instance and the prepared template/image identified by its launch receipt.

```bash
abx kill "$SANDBOX_ID"
```

`abx kill` deletes the sandbox, not reusable prepared templates or images. Follow the [cleanup guide](../docs/using-templates.md#cli-sdk-and-http) for resources created by your launch.

## Resources

2 vCPU, 2048 MB memory, port 9000. Headless Chromium uses `/tmp` rather than the
small `/dev/shm`; concurrent browser requests increase memory usage. Delete old
`browser-artifacts/` files through the files API to reclaim sandbox rootfs space.

## Contributing

To improve this template, see the [contribution guide](../CONTRIBUTING.md), [template specification](../docs/template-spec.md) and [design notes](../docs/design/browser-automation.md).

## Issues

Template tracking: [awesome-templates#22](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/22).
Report server/client defects to python-sdk and CLI defects to agent-sandbox with
`[templates]` in the title. Include redacted reproduction, provider, generation,
SDK commit, expected and actual results. Search existing issues first.

## License

Apache-2.0. Playwright is Apache-2.0; Chromium and bundled dependencies retain
their upstream notices.

Follow-up real build-network execution exceeded300seconds, so the earlier stream deadline is not a universal per-RUN cap. Stage separation is retained; slow large-asset transport remains unresolved.
