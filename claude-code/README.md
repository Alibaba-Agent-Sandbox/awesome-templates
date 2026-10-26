# claude-code

## What it does

Run unchanged official Claude Code2.0.76 headless planning and Read/Edit/Write/Bash tools. Existing `claude` retains its Anthropic-oriented API; new `claude_byok` explicitly uses an authored Messages-to-OpenAI-Chat text/tool adapter. Compatible-model use is experimental and [not supported by Anthropic](https://code.claude.com/docs/en/llm-gateway); no Claude-model/subscription/vendor endorsement claim.

## Stack

The default recipe uses the Alibaba FC generation-2 base, non-root `user`, and the published `agent-sandbox-server==0.4.0a6` package.

Original Claude Code `2.0.76`, Node.js 20, and the template text/tool protocol adapter for the explicit BYOK command.

[Dockerfile](Dockerfile) · [template.yaml](template.yaml) · [upstream notice](UPSTREAM-NOTICE.md)

## Problem solved

Use an installed tool in an isolated sandbox, submit work through CLI, Python or HTTP, then export the files. Configure model and cloud-sandbox credentials separately.

## Quick start (CLI)

Install the CLI/Python client and configure your platform (Sandbox API key, connection address and build image registry) using the [usage guide](../docs/using-templates.md#installation), then set the separate model/application credentials below. Launching the public recipe does not require a repository checkout.

The example uses `claude_byok`: the original Claude CLI plus the template's explicit text/tool adapter to your Chat Completions endpoint. It does not authenticate a Claude subscription or implement the entire Anthropic API. Supply all three `CLAUDE_MODEL_*` values; `ANTHROPIC_API_KEY` belongs to the separate `claude` command and is not reused. No browser login is started.

For the DashScope base below, create a Beijing-region key following [Model Studio API-key setup](https://www.alibabacloud.com/help/en/model-studio/get-api-key) and use a model allowed for that account. Other regions and Coding Plans use their matching keys/endpoints.

Replace every `<...>` placeholder with your own value; use an exact model ID available to your account. Set secrets in your own terminal or secret manager, never in the image, YAML or public logs. Configure these variables **before** launch; later host changes do not reconfigure the running application.

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export CLAUDE_MODEL_API_KEY='<your-model-or-vendor-key>'
export CLAUDE_MODEL_BASE_URL='https://dashscope.aliyuncs.com/compatible-mode/v1'
export CLAUDE_MODEL='<model-id-from-your-provider>'
abx template launch Alibaba-Agent-Sandbox/awesome-templates//claude-code --sandbox-timeout 1800 --yes
export SANDBOX_ID='<sandbox-id-returned-by-launch>'
abx sandbox command list "$SANDBOX_ID"
```

`--sandbox-timeout 1800` is the sandbox lifetime in seconds; `command_timeout`/`timeout_s` limits one task, while `ABX_HTTP_TIMEOUT`/SDK `timeout` controls client waiting. These are separate limits.

Launch starts this instance's application; do not create a second sandbox or second server. For OpenSandbox, follow its [setup](../docs/using-templates.md#cli-sdk-and-http) and set `ABX_PROVIDER=opensandbox`; the Python examples below read that same choice.

```bash
ABX_HTTP_TIMEOUT=660 abx run "$SANDBOX_ID" claude_byok --json-args '{"prompt":"Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.","allow_unsafe_tools":true,"cwd":"/home/user/app","command_timeout":300}'
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
            9000, token=os.environ["ABX_SERVER_TOKEN"], timeout=660
        )
        try:
            print(await client.commands.run('claude_byok', prompt='Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.', allow_unsafe_tools=True, cwd='/home/user/app', command_timeout=300))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

## Quick start (HTTP POST)

Use the [direct HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserving gateway headers, URL path/query and the independent application token. Send `POST /commands/claude_byok` with `Content-Type: application/json` and this direct argument object, without an `args` wrapper:

```json
{
  "prompt": "Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.",
  "allow_unsafe_tools": true,
  "cwd": "/home/user/app",
  "command_timeout": 300
}
```

The response is `{"result": ...}`; see the command reference for its actual content type. Model text varies. Set the HTTP wait to at least 660 seconds; the command execution deadline is separate, and disconnecting does not guarantee remote cancellation. Authentication failures return 401, invalid argument types 400, and execution errors an error response. If a result includes `exit_code`, also check that it is zero.

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
| claude_version | none | Original CLI `2.0.76 (Claude Code)`; no model |
| claude_native_check | none | Original cli.js hash and help flags: original_native/isolated_settings/no_session_persistence/strict_mcp booleans |
| claude_setup_check | none | Mode and model_key_set/model_base_set/model_set presence, vendor_account_verified:false/provider_default_fallback:false/requires_unsafe_optin:true; no values/network |
| claude_byok | prompt: required string1..32768UTF8bytes/nonempty/noNUL; cwd: default empty string, max4096bytes, existing resolved directory within WORKSPACE; command_timeout: integer1..600seconds default300, booleans rejected; allow_unsafe_tools: booleanFalse default, must explicitly be True for this disposable-sandbox bypass profile | stdout/exit_code0/native_completed/native_version/cli_sha256/model/permission_profile/protocol/model_calls/native_tool_results/relay_calls. Original tools edit project; no raw transcript |
| claude | prompt: required nonempty string; model: string default sonnet; cwd: string default empty/contained existing directory; allowed_tools: string default Read,Edit,Write; resume: string default empty; command_timeout: integer300/range1..900seconds | Native command JSON encoded as a string, sanitized for environment secrets. Uses existing Anthropic credential/settings behavior; bounded isolated BYOK guarantees do not certify this native provider mode |

Named-command results are buffered rather than streamed. `cwd` must be an existing directory satisfying the template's path constraints. Editing/tool permission allows model actions with the sandbox user's authority. Client disconnect is not a cancellation mechanism. Model calls are serialized; overlapping requests fail busy. Cleanup can extend response time; the examples leave an HTTP waiting margin.

## Configuration

| Name | Default / requirement | Meaning |
| --- | --- | --- |
| CLAUDE_MODEL_API_KEY | empty; required for BYOK | Explicit approved compatible upstream key; parent adapter only |
| CLAUDE_MODEL_BASE_URL | empty; required for BYOK | HTTPS Chat base/no userinfo/query/fragment/max2048chars; literal-loopback HTTP for fixed fixtures |
| CLAUDE_MODEL | empty; required for BYOK | Selected model1..200identifier characters |
| ANTHROPIC_API_KEY | empty; native provider mode only | Existing Anthropic-compatible native provider configuration; not silently reused by BYOK |
| WORKSPACE | /home/user/app | Existing project root |
| ABX_SERVER_TOKEN | required; empty declaration | Export an independent application token before the template launch; separate from model and gateway credentials |

New settings captured at module import. Key max8192/no control characters; no default provider/model/key fallback. Native/tool environment gets only an ephemeral local adapter token and minimal private HOME/config/cache; real upstream key remains in the parent and is sent only to exact configured Chat origin. Original command results and error messages omit credentials/private endpoints/transcripts. Same-user OS access remains; environment filtering/cwd containment is not another tenant boundary. Native resume/settings behavior is retained and outside BYOK isolation claims.

## Resources

2 vCPU, 2048 MB RAM, application port 9000, non-root `user`. Working directory: `/home/user/app`. Disk capacity and lifetime depend on the selected platform. Model tasks require outbound access to the configured model service and incur that service's charges. This pinned installation targets Linux x86_64.

## Contributing

To develop the template, read [CONTRIBUTING](../CONTRIBUTING.md) and the [design](../docs/design/claude-code.md).

## Issues

[Issue15](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/15), [template defects](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues), [Python SDK](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), [CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Original upstream behavior uses its support channels. Never attach credentials or private transcripts.

## License

Authored template/adapter: [Apache-2.0](../LICENSE). Original Anthropic package remains all rights reserved under its [original terms/notices](UPSTREAM-NOTICE.md); no relicensing or vendor endorsement.
