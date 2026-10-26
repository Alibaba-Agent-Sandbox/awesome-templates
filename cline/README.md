# cline

## What it does

Runs genuine official `cline@3.0.73` in bounded headless JSON/yolo mode. The CLI reads a prompt from anonymous stdin, edits the selected workspace using its native tools and returns buffered NDJSON plus its actual exit code. It uses an explicitly configured OpenAI-compatible provider; a Cline hosted account is not selected. This is the CLI product, with no VS Code extension or desktop UI claim.

## Stack

The default recipe uses the Alibaba FC generation-2 base, non-root `user`, and the published `agent-sandbox-server==0.4.0a6` package.

Official Cline CLI `3.0.73`, its Linux x86_64 native runtime, and Node.js `24.16.0`.

[Dockerfile](Dockerfile) · [template.yaml](template.yaml) · [upstream license](UPSTREAM-LICENSE.md)

## Problem solved

Use an installed tool in an isolated sandbox, submit work through CLI, Python or HTTP, then export the files. Configure model and cloud-sandbox credentials separately.

## Quick start (CLI)

Install the CLI/Python client and configure your platform (Sandbox API key, connection address and build image registry) using the [usage guide](../docs/using-templates.md#installation), then set the separate model/application credentials below. Launching the public recipe does not require a repository checkout.

This configured BYOK path speaks Chat Completions using your explicit key/base/model. A Cline account, GitHub token and interactive login are not required. The upstream agent runs in `--yolo` mode; file and shell tools can act with the sandbox user's permissions.

For the DashScope base below, create a Beijing-region key following [Model Studio API-key setup](https://www.alibabacloud.com/help/en/model-studio/get-api-key) and use a model allowed for that account. Other regions and Coding Plans use their matching keys/endpoints.

Replace every `<...>` placeholder with your own value; use an exact model ID available to your account. Set secrets in your own terminal or secret manager, never in the image, YAML or public logs. Configure these variables **before** launch; later host changes do not reconfigure the running application.

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export CLINE_MODEL_API_KEY='<your-model-or-vendor-key>'
export CLINE_MODEL_BASE_URL='https://dashscope.aliyuncs.com/compatible-mode/v1'
export CLINE_MODEL='<model-id-from-your-provider>'
abx template launch Alibaba-Agent-Sandbox/awesome-templates//cline --sandbox-timeout 1800 --yes
export SANDBOX_ID='<sandbox-id-returned-by-launch>'
abx sandbox command list "$SANDBOX_ID"
```

`--sandbox-timeout 1800` is the sandbox lifetime in seconds; `command_timeout`/`timeout_s` limits one task, while `ABX_HTTP_TIMEOUT`/SDK `timeout` controls client waiting. These are separate limits.

Launch starts this instance's application; do not create a second sandbox or second server. For OpenSandbox, follow its [setup](../docs/using-templates.md#cli-sdk-and-http) and set `ABX_PROVIDER=opensandbox`; the Python examples below read that same choice.

```bash
ABX_HTTP_TIMEOUT=420 abx run "$SANDBOX_ID" cline --json-args '{"prompt":"Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.","cwd":"/home/user/workspace","command_timeout":300}'
```

The task creates `generated_hello.py` and `GENERATED_REPORT.md` in `/home/user/workspace`. The example explicitly enables the required editing/tools; use an owned disposable sandbox. The SDK and HTTP examples are alternative ways to submit the same task; choose one.

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
            print(await client.commands.run('cline', prompt='Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.', cwd='/home/user/workspace', command_timeout=300))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

## Quick start (HTTP POST)

Use the [direct HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserving gateway headers, URL path/query and the independent application token. Send `POST /commands/cline` with `Content-Type: application/json` and this direct argument object, without an `args` wrapper:

```json
{
  "prompt": "Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.",
  "cwd": "/home/user/workspace",
  "command_timeout": 300
}
```

The response is `{"result": ...}`; see the command reference for its actual content type. Model text varies. Set the HTTP wait to at least 420 seconds; the command execution deadline is separate, and disconnecting does not guarantee remote cancellation. Authentication failures return 401, invalid argument types 400, and execution errors an error response. If a result includes `exit_code`, also check that it is zero.

### Export files and cleanup

```bash
abx exec "$SANDBOX_ID" -- python3 /home/user/workspace/generated_hello.py
abx download "$SANDBOX_ID" /home/user/workspace/generated_hello.py ./generated_hello.py
abx download "$SANDBOX_ID" /home/user/workspace/GENERATED_REPORT.md ./GENERATED_REPORT.md
abx kill "$SANDBOX_ID"
```

Expected program output: `Hello from the sandbox`. Inspect actual files before using them; a successful-looking model response does not guarantee files exist. Files do not automatically update the template or your machine; export them before deleting the sandbox.

`close()`/`aclose()` only close client connections; they do not delete the sandbox. Prepared templates/images in the launch journal can remain for reuse; remove only your own exact resources when no longer needed.

## Command reference

| Command | Parameters | Return / side effects |
| --- | --- | --- |
| cline_version | none | Actual pinned native version, `{"native_version":"3.0.73"}`; no model/auth |
| cline_setup_check | none | mode `openai-compatible-byok`; base_url_set/api_key_set/model_set booleans; cline_account_required:false; no network/secret values |
| cline | prompt: required nonempty string1..32768UTF-8 bytes, no NUL; cwd: optional string default empty, max4096bytes, existing directory resolved inside WORKSPACE; command_timeout: integer1..600seconds default300 | `{stdout:string,stderr:string,exit_code:int,native_version:"3.0.73"}`; native tool execution and workspace file changes |

Named-command results are buffered rather than streamed. `cwd` must be an existing directory satisfying the template's path constraints. Editing/tool permission allows model actions with the sandbox user's authority. Client disconnect is not a cancellation mechanism.

## Configuration

| Name | Required / default | Meaning |
| --- | --- | --- |
| CLINE_MODEL_API_KEY | model required; empty | Approved compatible endpoint key; only forwarded as native OPENAI_API_KEY |
| CLINE_MODEL_BASE_URL | model required; empty | Explicit HTTPS API base, literal localhost HTTP for authored development only; no userinfo/query/fragment; max2048characters |
| CLINE_MODEL | model required; empty | Actual model identifier, max200allowed identifier characters |
| WORKSPACE | `/home/user/workspace` | Existing workspace root |
| ABX_SERVER_TOKEN | required; empty declaration | Export an independent application token before the template launch; separate from model and gateway credentials |

Values are captured when commands.py loads. The wrapper writes only provider/model/base metadata into private0600settings, not a model key value; native key resolution uses its documented environment support. Native state is private and removed on return/failure. Global telemetry/auto-update and runtime file logging are disabled; public/private model catalog refresh is disabled. Cline config/data/team/MCP paths are per-call and no caller GitHub/cloud keys, alternate binary override or Cline account token is forwarded. Host operator credentials never enter the native coding process.

## Resources

2 vCPU, 4096 MB RAM, application port 9000, non-root `user`. Working directory: `/home/user/workspace`. Disk capacity and lifetime depend on the selected platform. Model tasks require outbound access to the configured model service and incur that service's charges. This pinned installation targets Linux x86_64.

## Contributing

To develop the template, read [CONTRIBUTING](../CONTRIBUTING.md) and the [design](../docs/design/cline.md).

## Issues

[Template Issue66](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/66). [SDK/server](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues) and [CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues) defects use `[templates]` prefixes. Keep credentials/private logs out of public reports.

## License

Wrapper and Cline: Apache-2.0. [Repository license](../LICENSE), [pinned upstream Cline license](UPSTREAM-LICENSE.md). Third-party runtime/dependencies retain their unmodified distribution notices; no hosted account or trademark rights are implied.
