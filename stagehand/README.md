# stagehand

[中文](README.zh-CN.md)

## What it does

Runs the genuine Node.js `@browserbasehq/stagehand@4.3.0` SDK and its bundled browser extension against a private local Chromium. A bounded call performs one upstream `act` instruction, optionally extracts a `{text: string}` result with native `extract`, and writes a fresh PNG. It is a local browser slice; Browserbase hosted sessions, login persistence, full autonomous planning and arbitrary extraction schemas are outside this template's contract.

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a6`, installed directly by the Dockerfile.

Alibaba generation2 base v0.0.49, SHA256-pinned Node24.16.0, npm integrity-locked Stagehand4.3.0/Zod4.4.3 with the disclosed exact-source connect-parameter patch, Playwright1.58.0 Chromium1208/145.0.7632.6, Python3.13 and published server package. Runtime is non-root user; app `/home/user/app`, port9000. [Dockerfile](Dockerfile), [lockfile](package-lock.json), [design](../docs/design/stagehand.md).

## Problem solved

Expose real Stagehand semantic browser actions through the Agent Sandbox named-command API without requiring a Browserbase account. Native4.3.0 does not accept a custom base URL in ModelConfig. The documented upstream ClientLLM callback maps structured text/image requests to an explicitly configured OpenAI-compatible Chat Completions endpoint; DOM interpretation, selector choice, browser actions and extraction still use the actual SDK/extension. No substitute browser agent or fake CLI is installed.

## Quick start (CLI)

CLI, SDK and HTTP are alternative ways to use the same application. Choose one for the task. Examples may write files, create projects or start services; do not repeat the full example on the same instance without cleaning its previous outputs.

Install the CLI/Python SDK and configure your platform with the [usage guide](../docs/using-templates.md#installation). The platform API key creates sandboxes; `ABX_SERVER_TOKEN` independently protects this template application. Run the following in your own terminal; cloning this repository is unnecessary.

Fill in model settings before launch: the API key, endpoint and model ID must belong to the same model service and region. `https://model.example.invalid/v1` is a placeholder; replace it with your vendor API base, not a web chat URL. Use a model ID actually available at that endpoint.

This entry uses a model API key: no browser OAuth login is required, and your local logged-in account is not imported. See Configuration for protocol requirements. This template uses **Chat Completions**; an “OpenAI-compatible” label alone does not establish support for that API.

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export STAGEHAND_API_KEY='<your-model-api-key>'
export STAGEHAND_BASE_URL='https://model.example.invalid/v1'
export STAGEHAND_MODEL='<your-model-id>'
export ABX_HTTP_TIMEOUT=450
abx template launch Alibaba-Agent-Sandbox/awesome-templates//stagehand --sandbox-timeout 1800 --yes
# Paste the sandbox ID from the launch output
export SANDBOX_ID='paste-id-from-launch-output'
abx sandbox command list "$SANDBOX_ID"
```

```bash
abx run "$SANDBOX_ID" stagehand --json-args '{"task":"Click the More information link.","url":"https://example.com","extract_instruction":"Return the visible heading.","command_timeout":180}'
```

Returns native `action`, `extracted`, final URL and a fresh `screenshot_path`. Inspect `action.success`; the model may fail to complete its instruction.

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
            result = await client.commands.run('stagehand', task='Click the More information link.', url='https://example.com', extract_instruction='Return the visible heading.', command_timeout=180)
            print(result)
            Path('stagehand.png').write_bytes(await sb.files.read_bytes(result['screenshot_path']))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

The SDK returns the command value; it unwraps the HTTP `result` envelope. Closing the client does not delete the sandbox.

## Quick start (HTTP POST)

Resolve port 9000 on the same instance with the [HTTP calling example](../docs/using-templates.md#cli-sdk-and-http). Preserve gateway headers, URL path and query before adding the independent application authentication.

`POST /commands/stagehand`

```json
{
  "task": "Click the More information link.",
  "url": "https://example.com",
  "extract_instruction": "Return the visible heading.",
  "command_timeout": 180
}
```

Use `Content-Type: application/json` and application authentication as described in the shared guide. The request body is the direct argument object, without an `args` wrapper. Success returns `{"result": ...}` with the value described above. Set the HTTP client wait to 450 seconds, separately from the command execution deadline. Responses are buffered, not event streams. Errors: 400 invalid arguments, 401 authentication, 404 unknown command, 500 execution failure.

## Command reference

| Command | Parameters | Result / side effects |
| --- | --- | --- |
| stagehand_version | none | Actual installed SDK version `4.3.0`; no browser/model |
| stagehand_setup_check | none | Boolean `api_key_set`, `base_url_set`, `model_set`; mode; `browserbase_account_required:false`; no network/secrets |
| stagehand_self_test | none | `STAGEHAND_NATIVE_OK`; new private offline browser, title/PNG and cleanup;60s deadline |
| stagehand | `task`: required nonempty string; `url`: required HTTP(S) without userinfo/control/whitespace; `extract_instruction`: optional string default empty; `command_timeout`: integer1..600seconds default180 | Actual native action, optional text extraction and new PNG; private local browser per call |

Task and extraction instructions each cap32768UTF-8 bytes; URL caps8192. Return object: `version`, `sdk_sha256`, `title`, `final_url`, `action:{success,message,actionDescription,actions}`, `extracted:null` or `{text}`, `model_calls` (at most8), `screenshot_path` and `png_bytes`. The unique artifact is `/home/user/app/stagehand-artifacts/<random>.png` (or under WORKSPACE); PNG caps8MiB. Read it through `sb.files.read_bytes` and delete only that returned artifact after use. No existing caller file is overwritten. Calls run serially; overlap fails explicitly instead of replacing an active process. Native stdout/stderr each cap256KiB; private upstream errors are omitted; nonzero exit/deadline/cleanup uncertainty fails.

## Configuration

This entry calls compatible Chat Completions. Include the vendor API prefix (often `/v1`) in the base; do not append `/chat/completions`. The model must return JSON-schema structured output and support image content sent by the native flow.

| Variable | Required / default | Meaning |
| --- | --- | --- |
| STAGEHAND_API_KEY | required for model; empty | Approved compatible endpoint credential; never a Browserbase token |
| STAGEHAND_BASE_URL | required for model; empty | HTTPS API base ending in your endpoint's API prefix; literal localhost HTTP allowed for development; no userinfo/query/fragment; appends `/chat/completions` |
| STAGEHAND_MODEL | required for model; empty | Actual model identifier, at most200 allowed identifier characters |
| ABX_SERVER_TOKEN | required; empty declaration | Export an independent application token before the template launch; separate from model and gateway credentials |
| WORKSPACE | `/home/user/app` | Existing artifact root |

The wrapper uses upstream ClientLLM structured generation, maps text/images and requires complete JSON-schema model replies. Requests cap2MiB, replies1MiB, each inference60seconds; no redirects, retries or provider fallback. Model values are captured at server import. Secrets enter the Node consumer via anonymous stdin memory, never argv, browser environment or credential files. Browser subprocesses inherit only selected runtime/certificate variables and new private HOME/cache/profile. Native Chromium sandbox is explicitly disabled inside the outer disposable sandbox; it is not a tenant/security boundary. Pages can reach networks accessible to that sandbox; authenticate/trust named-command callers accordingly.


Pinned compatibility profile: SDK4.3.0 accepts extensionId in its local connect schema but drops it in the factory. [patch_sdk.py](patch_sdk.py) requires pristine SDK SHA25638ec56a2a1af1fb72c3e361a66b256def8e3665cca527e0d337f8a76a8308bd1 and changes one forwarding site. The owned Chrome launcher preloads only the unchanged bundled extension, observes its actual service-worker ID and uses native localBrowser.connect/Stagehand.create/act/extract. Runtime and independent controller require patched SDK SHA256bdf3cd62126c1529e8a889cae17fd098303e24e962e491a4b20786de72c369e0. This is a disclosed patched upstream distribution. Bounded failure diagnostics expose only allowlisted phase/status/call count, never upstream response bodies, private endpoints or key values.

The working directory is `/home/user/app`. Artifacts remain on the sandbox disk; export anything needed before deleting the instance. Delete only your own instance and the prepared template/image identified by its launch receipt.

```bash
# Replace <returned-path> with screenshot_path from the result
abx download "$SANDBOX_ID" '<returned-path>' ./stagehand.png
abx kill "$SANDBOX_ID"
```

`abx kill` deletes the sandbox, not reusable prepared templates or images. Follow the [cleanup guide](../docs/using-templates.md#cli-sdk-and-http) for resources created by your launch.

## Resources

2vCPU,4096MB RAM, port9000, about10GiB Express rootfs. No Docker/KVM/GPU needed inside the sandbox. The image enforces an8GiB rootfs budget. Local browser/extension startup and compatible model structured output are required. Browserbase cloud/cache/services are not used by this entry.

## Contributing

To improve this template, see the [contribution guide](../CONTRIBUTING.md), [template specification](../docs/template-spec.md) and [design notes](../docs/design/stagehand.md).

## Issues

[Template Issue68](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/68). [SDK/server](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues) and [CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues) defects use `[templates]` prefixes. Never include credentials or private logs.

## License

Wrapper: [Apache-2.0](../LICENSE). Stagehand and Zod: MIT; retain [upstream Stagehand license](UPSTREAM-LICENSE.md). Chromium/Node and their dependencies retain upstream notices/licenses in their unmodified distributions. No SaaS software or vendor account rights are implied.
