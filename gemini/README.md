# gemini

## What it does

Run original official Google Gemini CLI0.64.0 planning and text/file/shell tools. Existing gemini/setup/version APIs remain; gemini_byok adds explicit compatible Chat transport through an authored GenerateContent-to-Chat text/tool adapter. Original CLI/tool engine is unchanged; Google Gemini model access, OAuth, hosted subscriptions and full feature compatibility are not claimed. [Official configuration](https://geminicli.com/docs/reference/configuration/).

## Stack

The default recipe uses the Alibaba FC generation-2 base, non-root `user`, and the published `agent-sandbox-server==0.4.0a6` package.

Original Gemini CLI `0.64.0`, Node.js 20, and the template text/tool protocol adapter for the explicit BYOK command.

[Dockerfile](Dockerfile) · [template.yaml](template.yaml) · [upstream notice](UPSTREAM-NOTICE.md)

## Problem solved

Use an installed tool in an isolated sandbox, submit work through CLI, Python or HTTP, then export the files. Configure model and cloud-sandbox credentials separately.

## Quick start (CLI)

Install the CLI/Python client and configure your platform (Sandbox API key, connection address and build image registry) using the [usage guide](../docs/using-templates.md#installation), then set the separate model/application credentials below. Launching the public recipe does not require a repository checkout.

The example uses `gemini_byok`: the original Gemini CLI with the template's explicit text/tool adapter to Chat Completions. Supply the three `GEMINI_BYOK_*` settings; Google login and `GEMINI_API_KEY` are not required for that path. The separate `gemini` command uses the native Google authentication/model settings. A compatible-model key does not become a Google account credential.

For the DashScope base below, create a Beijing-region key following [Model Studio API-key setup](https://www.alibabacloud.com/help/en/model-studio/get-api-key) and use a model allowed for that account. Other regions and Coding Plans use their matching keys/endpoints.

Replace every `<...>` placeholder with your own value; use an exact model ID available to your account. Set secrets in your own terminal or secret manager, never in the image, YAML or public logs. Configure these variables **before** launch; later host changes do not reconfigure the running application.

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export GEMINI_BYOK_API_KEY='<your-model-or-vendor-key>'
export GEMINI_BYOK_BASE_URL='https://dashscope.aliyuncs.com/compatible-mode/v1'
export GEMINI_BYOK_MODEL='<model-id-from-your-provider>'
abx template launch Alibaba-Agent-Sandbox/awesome-templates//gemini --sandbox-timeout 1800 --yes
export SANDBOX_ID='<sandbox-id-returned-by-launch>'
abx sandbox command list "$SANDBOX_ID"
```

`--sandbox-timeout 1800` is the sandbox lifetime in seconds; `command_timeout`/`timeout_s` limits one task, while `ABX_HTTP_TIMEOUT`/SDK `timeout` controls client waiting. These are separate limits.

Launch starts this instance's application; do not create a second sandbox or second server. For OpenSandbox, follow its [setup](../docs/using-templates.md#cli-sdk-and-http) and set `ABX_PROVIDER=opensandbox`; the Python examples below read that same choice.

```bash
ABX_HTTP_TIMEOUT=420 abx run "$SANDBOX_ID" gemini_byok --json-args '{"prompt":"Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.","allow_unsafe_tools":true,"cwd":"/home/user/app","command_timeout":300}'
```

The task creates `generated_hello.py` and `GENERATED_REPORT.md` in `/home/user/app`. The example explicitly enables the required editing/tools; use an owned disposable sandbox. The SDK and HTTP examples are alternative ways to submit the same task; choose one.

## Quick start (Python SDK)

In your virtual environment, run `python -m pip install agent-sandbox-client==0.4.0a6`.

```python
import asyncio
import os
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.connect(
        os.environ["SANDBOX_ID"], provider=os.environ["ABX_PROVIDER"]
    )
    try:
        client = await sb.application_client(
            9000, token=os.environ["ABX_SERVER_TOKEN"], timeout=420
        )
        try:
            print(await client.commands.run('gemini_byok', prompt='Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.', allow_unsafe_tools=True, cwd='/home/user/app', command_timeout=300))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

## Quick start (HTTP POST)

Use the [direct HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserving gateway headers, URL path/query and the independent application token. Send `POST /commands/gemini_byok` with `Content-Type: application/json` and this direct argument object, without an `args` wrapper:

```json
{
  "prompt": "Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.",
  "allow_unsafe_tools": true,
  "cwd": "/home/user/app",
  "command_timeout": 300
}
```

The response is `{"result": ...}`; see the command reference for its actual content type. Model text varies. Set the HTTP wait to at least 420 seconds; the command execution deadline is separate, and disconnecting does not guarantee remote cancellation. Authentication failures return 401, invalid argument types 400, and execution errors an error response. If a result includes `exit_code`, also check that it is zero.

### Export files and cleanup

```bash
abx exec "$SANDBOX_ID" -- python3 /home/user/app/generated_hello.py
abx download "$SANDBOX_ID" /home/user/app/generated_hello.py ./generated_hello.py
abx download "$SANDBOX_ID" /home/user/app/GENERATED_REPORT.md ./GENERATED_REPORT.md
abx kill "$SANDBOX_ID"
```

Expected program output: `Hello from the sandbox`. Inspect actual files before using them; a successful-looking model response does not guarantee files exist. Files do not automatically update the template or your machine; export them before deleting the sandbox.

`close()`/`aclose()` only close client connections; they do not delete the sandbox. Prepared templates/images in the launch journal can remain for reuse; remove only your own exact resources when no longer needed.

## Command reference

| Command | Parameters | Result / effects |
| --- | --- | --- |
| gemini_version | none | Original CLI0.64.0; no model |
| gemini_native_check | none | Exact original449file identity plus actual help flags original_native/headless_json/explicit_approval/owned_project_include |
| gemini_byok_setup_check | none | mode/model_key_set/model_base_set/model_set, vendor_account_verified:false/provider_default_fallback:false/requires_unsafe_optin:true; no values/network |
| gemini_byok | prompt required nonempty1..32768UTF8bytes/noNUL; cwd default empty string/max4096bytes/existing resolved directory within WORKSPACE; command_timeout integer1..600seconds/default300/no bool; allow_unsafe_tools booleanFalse, must explicitly be True on an owned disposable sandbox | stdout/exit_code0/native_completed/permission_profile:explicit-owned-sandbox-bypass/native_version/archive_sha256/model/protocol/model_calls/native_tool_results/relay_calls; native tools modify caller project; no raw transcript |
| gemini_setup_check | none | Legacy installed/version/pinned_version/key/model presence/workspace/settings path/existence/JSON-validity inspection; no changes/authentication |
| gemini | prompt required nonempty string; model default empty string then GEMINI_MODEL then gemini-3.1-flash-lite; cwd default empty/contained existing directory; command_timeout integer600/range1..1800seconds; yolo booleanFalse | Legacy original buffered JSON string. yoloFalse selects plan, True explicitly permits tool execution. Requires GEMINI_API_KEY, no implicit OpenAI-key/OAuth fallback. New BYOK isolation guarantees do not certify native provider mode |

Named-command results are buffered rather than streamed. `cwd` must be an existing directory satisfying the template's path constraints. Editing/tool permission allows model actions with the sandbox user's authority. Client disconnect is not a cancellation mechanism. Model calls are serialized; overlapping requests fail busy. Cleanup can extend response time; the examples leave an HTTP waiting margin.

## Configuration

| Name | Default / requirement | Meaning |
| --- | --- | --- |
| GEMINI_BYOK_API_KEY | empty; required for BYOK | Explicit compatible upstream key, parent adapter only |
| GEMINI_BYOK_BASE_URL | empty; required for BYOK | HTTPS Chat base/max2048chars/no userinfo/query/fragment; literal-loopback HTTP for fixtures |
| GEMINI_BYOK_MODEL | empty; required for BYOK | Actual selected identifier1..200allowed characters |
| GEMINI_API_KEY | empty; legacy only | Existing Google/native-compatible key; BYOK never silently reuses it |
| GEMINI_MODEL | gemini-3.1-flash-lite; legacy only | Existing legacy default; separate from explicit BYOK selection |
| WORKSPACE | /home/user/app | Existing caller project root |
| ABX_SERVER_TOKEN | required; empty declaration | Export an independent application token before the template launch; separate from model and gateway credentials |

BYOK settings captured at module import; key max8192/no control characters. Native environment has only fresh local adapter token, minimal PATH and private HOME/config/cache; real upstream key is sent only to exact approved Chat origin. Same-user OS access remains; cwd/environment filters are not another tenant boundary. Existing native provider configuration behavior stays separate. No private endpoints/keys/transcripts in results or errors.

## Resources

2 vCPU, 4096 MB RAM, application port 9000, non-root `user`. Working directory: `/home/user/app`. Disk capacity and lifetime depend on the selected platform. Model tasks require outbound access to the configured model service and incur that service's charges. This pinned installation targets Linux x86_64.

## Contributing

To develop the template, read [CONTRIBUTING](../CONTRIBUTING.md) and the [design](../docs/design/gemini.md).

## Issues

[Issue30](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/30), [templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues), [Python SDK](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), [CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Original upstream behavior uses upstream channels. Never attach credentials/private transcripts.

## License

Authored template/adapter and original Gemini CLI are Apache-2.0 under their respective original [licenses/notices](UPSTREAM-NOTICE.md); retain bundled third-party terms. [Repository license](../LICENSE). No Google endorsement or hosted model access claim.
