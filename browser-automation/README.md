# browser-automation

## What it does

Python browse/scrape/fill_form requests each own a separate browser. Native MCP calls deliberately share one owned browser session until stop or idle close; mcp_stop removes its private profile/output.

Navigate with headless Chromium, save PNG screenshots, extract text and links,
and fill forms. Each named command owns and closes a fresh browser; concurrent
requests do not share cookies, DOM state, or form values. Form filling verifies
input values internally and returns only a count. It does not submit the form.

## Stack

Alibaba runtime base (default `v0.0.49`, Python 3.13); Playwright `1.58.0` with
its matching Chromium revision; pinned `agent-sandbox-server` archive in the
Dockerfile. Browser launches use `--disable-dev-shm-usage` for the Express 64 MB
shared-memory limit. This template exposes named commands, files and process
APIs; optional built-in `/browser/*` endpoints are not enabled.

## Problem solved

Give an agent reproducible browser operations and downloadable artifacts without
requiring Docker, KVM, a desktop, a model API key, or a persistent browser session.

## Quick start (CLI)

Check the installed entry with `abx create --help`. The complete example below uses native CLI syntax. If help lists `--detach`, use the standard Express entry: create with `abx create <template-id> --detach` and clean up with `abx kill <sandbox-id>` without `-y`; named commands through `abx run` are unchanged. See the [entry comparison](../docs/using-templates.md#client-entry-compatibility).

Runtime configuration: the create-time key examples below require the named-command server to start with those values. For a prewarmed server, inspect its setup flags when provided and follow [explicit process configuration](../docs/runtime-environment.md); creating a sandbox does not reconfigure an already running server.

```bash
abx template install alibaba-agent-sandbox/awesome-templates//browser-automation
abx create --template <template-id>
abx run <sandbox-id> browse --arg url=https://example.com --arg action=extract
abx run <sandbox-id> browse --json-args '{"url":"https://example.com","action":"screenshot","timeout_s":30}'
abx run <sandbox-id> scrape --arg url=https://example.com --arg selector=h1
```

Use the installed template id and sandbox id returned by the CLI. `abx run`
invokes named commands. `abx exec` runs shell programs. `--arg` passes strings;
use `--json-args` for typed integer `timeout_s`. Do not put real form secrets on
the command line or in shell history; use the SDK from a secret-aware process.

## Quick start (Python SDK)

The client distribution is `agent-sandbox-client` (import `agent_sandbox`). Until the matching release is available, use the [paired, pinned source installation](../docs/python-client-installation.md).

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=300)
    try:
        result = await sb.run("browse", url="https://example.com", action="extract", timeout=90)
        print(result["title"])
        screenshot = await sb.run("browse", url="https://example.com", action="screenshot", timeout=90)
        await sb.server.files.download_file(screenshot["path"], "example.png")
        print(sb.network.get_url(9000))
    finally:
        await sb.kill()

asyncio.run(main())
```

`sb.run` returns the unwrapped `result`. `timeout=90` is the client HTTP timeout;
command `timeout_s=30` defaults to 30 seconds per browser launch/navigation/action,
not a wall-clock deadline for the whole command. Each form field may consume one
action timeout. A client timeout does not guarantee cancellation. Use the process
API for background browser scripts, reconnecting and cancellation. With
`ABX_SERVER_TOKEN`, use `sb.server_at(9000, token=server_token, timeout=90).commands.run(...)`.

## Quick start (HTTP POST)

`BASE_URL` is the sandbox's port 9000 URL from `sb.network.get_url(9000)`.
For an unauthenticated local server:

```bash
curl --fail-with-body -X POST "$BASE_URL/commands/browse" \
  -H 'Content-Type: application/json' \
  --data '{"url":"https://example.com","action":"extract","timeout_s":30}'
```

Response shape (page text may change):

```json
{"result":{"action":"extract","title":"Example Domain","text":"Example Domain\n..."}}
```

Send the argument object directly, without an `args` wrapper. Server authentication
is optional: if `ABX_SERVER_TOKEN` was injected when creating the sandbox, add
`Authorization: Bearer ${SERVER_TOKEN}` or `X-Access-Token: ${SERVER_TOKEN}`.
Provider gateway authentication is separate: use the access headers returned by
`sb.network.get_access_headers()` when required by that provider. The Express port
9000 URL is currently public at the gateway; do not send its sandbox access token
as a server token. When both layers require credentials, preserve the server
Authorization header and the provider's distinct gateway header. Never log either.

HTTP 400 means missing or mistyped arguments, 401 means server authentication
failed, 404 means an unknown command, and 500 means browser/script failure or
semantic validation (invalid action, URL, range, or form JSON). Errors use
`{"error":"...","type":"..."}`. Browser execution errors omit request values.

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

Version2.1.0 adds official `@playwright/mcp@0.0.83`, lockfile-pinned JavaScript Playwright1.64.0-alpha-1790635538000 and reuses the existing Chromium1208. No second Chromium or model credential is installed. The Python browser API remains pinned1.58.0. Both actual driver/browser combinations require acceptance; an npm version alone is not browser proof.

| Command | Parameters | Result |
| --- | --- | --- |
| mcp_start | none | running, port8931, mcp_version and negotiated protocol_version |
| mcp_status | none | running:false or current owned MCP status |
| mcp_call | method:str required, tools/list or tools/call or ping; params_json:str="{}", JSON object up to64KiB | actual MCP result object; inspect isError for tool failures |
| mcp_stop | none | running:false after owned process/browser/listener cleanup |
| mcp_self_test | none | PLAYWRIGHT_MCP_OK only after actual initialization/tools, two browser clicks independently observed by an owned HTTP fixture, real PNG screenshot and cleanup |

Run `abx run <sandbox-id> mcp_start`, then `abx run <sandbox-id> mcp_call --arg method=tools/list`. Inside that same sandbox a standard MCP client uses `http://127.0.0.1:8931/mcp` with the native MCP HTTP session/protocol headers. The listener is private to the sandbox;8931 is not an authenticated public gateway. Outside clients use SDK `await sb.run("mcp_call", method="tools/list")` through the command server's configured bearer authentication. For browser_click, the pinned upstream schema uses `target` from a fresh browser_snapshot; it does not use the old ref argument.

A process-start diagnostic `MCP_NODE_MODULES` may select an independently installed exact lockfile tree; production uses /opt/playwright-mcp/node_modules. MCP HOME/profile/output are private and deleted on stop; no saved browser/profile/extensions are loaded. Default action/navigation limits10/20seconds, HTTP response4MiB, native output-file eviction threshold10MiB (not a hard disk quota) and idle browser60seconds. Calls are serialized; streaming stays on the native in-sandbox MCP endpoint, while mcp_call returns a buffered result. Native child environment excludes operator cloud/model/server keys and Node injection variables. Browser navigation shares the sandbox's egress authority; no SSRF policy is added. Caller requests, page data and results can be private and must not be publicly logged.

### PDF and bounded workspace scripts

`pdf(url:str, landscape:bool=false, print_background:bool=true, timeout_s:int=30) -> {path,bytes,format:"PDF"}` renders A4 using the pinned real Chromium. URL supports the same schemes as browse, up to256KiB/no NUL. The generated workspace PDF is capped at16MiB after rendering; this is not a peak-memory bound. Boolean flags are typed. Read the artifact with SDK `await sb.files.read_bytes(result["path"])` and remove it after export. `abx run <sandbox-id> pdf --arg url='data:text/html,<h1>PDF proof</h1>'` exercises the actual renderer. No caller output filename is overwritten; symlink artifact directories are refused.

PDF execution runs in a private-HOME child with its own1–120second execution deadline and bounded teardown. Generic run now also reserves process identity and stops marked detached/ordinary children on success, failure, overflow or deadline. stdout/stderr are each capped at256KiB; native diagnostics are omitted from errors. run preserves caller HOME but forwards only PATH/locale/browser/CA settings, excluding server/cloud/model keys and injected loaders. Use the SDK process interface for explicit long-lived background work/environment settings. This process hygiene is not a second sandbox security boundary. Build enforces actual du rootfs accounting at8GiB; disk free-space size is a separate quantity.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `PLAYWRIGHT_BROWSERS_PATH` | `/opt/playwright` in the image | Shared readable Chromium installation |
| `WORKSPACE` | `/home/user/app` | Script root and `browser-artifacts/` output root; keep aligned with the server file policy |
| `ABX_SERVER_TOKEN` | unset/empty | Optional server authentication, injected at sandbox creation |
| `ABX_SERVER_PORT` | `9000` | Local `python3 commands.py` server port |

Outputs from extraction, screenshots, links and user scripts may contain sensitive
page content. Treat artifacts as private; do not print them into shared logs.
Never bake credentials into images or YAML. Form errors and success responses do
not echo entered values. User scripts are responsible for their own stdout.

## Resources

2 vCPU, 2048 MB memory, port 9000. Headless Chromium uses `/tmp` rather than the
small `/dev/shm`; concurrent browser requests increase memory usage. Delete old
`browser-artifacts/` files through the files API to reclaim sandbox rootfs space.

## Verified


### Current image acceptance — 2026-10-22

| Provider | Current version and scope | Evidence |
| --- | --- | --- |
| alicloud-express | 2.2.0; regular image, actual CLI/SDK, complete HTTP 37 PASS / 0 FAIL / 0 SKIP, independent sandbox/template/private-registry cleanup | [Runtime and HTTP receipt](evidence/image-http-2026-10-22T101142Z.json) |
| opensandbox | 2.2.0; original Docker backend, every CLI/SDK named smoke, complete HTTP 37 PASS / 0 FAIL / 0 SKIP, independent SDK/container/process cleanup | [Native source image receipt](evidence/opensandbox-2026-10-22T110653Z.json) |

OpenSandbox CLI smoke uses actual `abx exec` into the guest named HTTP API. Generic `run_code` remains unsupported and `template launch` capability checks still apply. Missing model/vendor-account checks remain explicit skips in the receipts and do not establish model acceptance. [Reproduction and scope](../docs/source-image-acceptance.md).

<details>
<summary>Earlier acceptance records (original dates and scope retained)</summary>

Version2.2.0 passed actual Alibaba Express native steps and Python SDK Sandbox.create, CLI/SDK browser/MCP smoke and full remote HTTP **37 PASS / 0 FAIL / 0 SKIP**. Independent files HTTP verified screenshot PNG and both portrait/landscape PDF bytes and geometry; owned artifacts/processes and sandbox/template cleanup were confirmed. The source build includes the8GiB rootfs gate. Model acceptance was not run; other providers and unexercised MCP actions remain unverified.

| Version | Provider | Evidence |
| --- | --- | --- |
| 2.2.0 | alicloud-express | [SDK-created steps](evidence/express-2026-10-20T103410Z.json), [full HTTP37](evidence/full-http-steps-2026-10-20T103410Z.json) |

Prior2.1.0 receipts below retain their original version.

</details>

## Historical2.1.0 verification


Version2.1.0 passed actual Alibaba Express native steps, Python SDK Sandbox.create, CLI/SDK browser and native MCP smoke, and full remoteHTTP29 PASS/0 FAIL/0 SKIP. Native MCP discovery and actual navigation/snapshot/click/screenshot use the existing Chromium1208; the independent counter and PNG checks passed. Owned sandbox/template deletion and independent absence were confirmed. Other providers and all remaining upstream tool actions are not certified.

| Version | Provider | Evidence |
| --- | --- | --- |
| 2.1.0 | alicloud-express | [SDK-created steps](evidence/express-2026-10-20T094547Z.json), [full HTTP29](evidence/full-http-steps-2026-10-20T094547Z.json) |

## Historical2.0.2 verification

Version 2.0.2 passed actual CI-image registration, official READY, CLI/SDK and complete Chromium screenshot/independent artifact HTTP 24 PASS / 0 FAIL / 0 SKIP. Independently confirmed sandbox/template/registry cleanup. Status remains experimental; other providers are unverified.

| Provider | Scope | Evidence |
| --- | --- | --- |
| alicloud-express | Historical2.0.2, actual image and independently verified cleanup | [canonical receipt](evidence/express-2026-10-20.json), [HTTP](evidence/image-http-2026-10-20T060053Z.json) |


The separate platform-step attempt did not reach READY within 1200 seconds; last official state was building. It is a [retained failure](evidence/full-http-steps-2026-10-20T062809Z.json), not step qualification.

## Historical verification

The following text records the original unqualified state; later dated receipts above supersede that status.

Local browser acceptance and static conformance can be run independently. They
are not cloud-provider acceptance. L1 requires an actual image build; L2 requires
a READY sandbox and external CLI and SDK calls. Missing Chromium fails L0;
a skipped browser suite cannot count as acceptance.

## Secondary development

Version2.0.2 separates Python package installation, system dependencies and
Chromium download into three RUN steps after an observed RUN stream deadline.
A later successful build diagnostic exceeded300 seconds; there is no verified universal per-RUN cap. Playwright and the full Chromium profile are unchanged;
older version receipts remain history.


Build from this directory using `abx template deploy` or the install command
above. The deployer replaces Alibaba region/tag placeholders and can inject a
server wheel from `ABX_SERVER_SDK_SOURCE`; the archive pin remains the fallback.
Keep heavyweight installs before the final `COPY commands.py`. Dockerfile has
no `CMD`/`ENTRYPOINT`; generation 2 uses YAML `start_cmd` and `ready_cmd` as `user`.

For local tests, install the pinned Playwright and matching Chromium in a writable
cache. Set `PLAYWRIGHT_BROWSERS_PATH` consistently for installation and execution.
Start `python3 commands.py` with `WORKSPACE` and `ABX_SERVER_BASE_DIR` pointing at
the same writable directory, then run `E2E_BASE_URL=http://127.0.0.1:9000 python3 e2e_test.py`.
The suite navigates inline pages, downloads real PNGs over the server files API,
checks form redaction and concurrency, and exits nonzero without Chromium.

### Agent Sandbox platform steps

From a repository checkout, `python scripts/run_steps_e2e.py browser-automation` builds and verifies this template through real Express platform steps. See [preparation, credentials, exact build provenance and cleanup](../docs/platform-steps.md). A model-free step smoke does not establish L3.

## Contributing

Follow [CONTRIBUTING.md](../CONTRIBUTING.md), the bilingual
[template spec](../docs/template-spec.md), and
[design](../docs/design/browser-automation.md). Run
`python3 scripts/check_template.py browser-automation` and
`python3 scripts/run_local_e2e.py` from the repository root. Record actual levels;
keep catalog status experimental until all required acceptance levels pass.

## Issues

Template tracking: [awesome-templates#22](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/22).
Report server/client defects to python-sdk and CLI defects to agent-sandbox with
`[templates]` in the title. Include redacted reproduction, provider, generation,
SDK commit, expected and actual results. Search existing issues first.

## License

Apache-2.0. Playwright is Apache-2.0; Chromium and bundled dependencies retain
their upstream notices.

Follow-up real build-network execution exceeded300seconds, so the earlier stream deadline is not a universal per-RUN cap. Stage separation is retained; slow large-asset transport remains unresolved.
