# Crush

[中文](README.zh-CN.md).

## What it does

Runs the official native Crush0.98.1 terminal agent using an explicitly configured OpenAI-compatible provider. Default turns expose no tools; allow_tools=true exposes exactly bash/edit/multiedit/view/write/ls/glob/grep. Subagent, MCP, network-fetch, background-job and LSP tools are disabled.

## Stack

The default recipe uses the Alibaba FC generation-2 base, non-root `user`, and the published `agent-sandbox-server==0.4.0a6` package.

Official Crush `0.98.1`; the Dockerfile selects a checksum-pinned GNU Linux x86_64/aarch64 release archive.

[Dockerfile](Dockerfile) · [template.yaml](template.yaml)

## Problem solved

Use an installed tool in an isolated sandbox, submit work through CLI, Python or HTTP, then export the files. Configure model and cloud-sandbox credentials separately.

## Quick start (CLI)

Install the CLI/Python client and configure your platform (Sandbox API key, connection address and build image registry) using the [usage guide](../docs/using-templates.md#installation), then set the separate model/application credentials below. Launching the public recipe does not require a repository checkout.

This headless path uses the three explicit model settings below; it does not run browser/OAuth login. The endpoint must support OpenAI-compatible Chat Completions and tool calls. Obtain the key and exact model ID from that endpoint's provider; a cloud Sandbox API key is a different credential. The example below uses DashScope's public compatible base as an example: use a key and model authorized for that same region, or replace all three together.

For the DashScope base below, create a Beijing-region key following [Model Studio API-key setup](https://www.alibabacloud.com/help/en/model-studio/get-api-key) and use a model allowed for that account. Other regions and Coding Plans use their matching keys/endpoints.

Replace every `<...>` placeholder with your own value; use an exact model ID available to your account. Set secrets in your own terminal or secret manager, never in the image, YAML or public logs. Configure these variables **before** launch; later host changes do not reconfigure the running application.

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export CRUSH_API_KEY='<your-model-or-vendor-key>'
export CRUSH_BASE_URL='https://dashscope.aliyuncs.com/compatible-mode/v1'
export CRUSH_MODEL='<model-id-from-your-provider>'
abx template launch Alibaba-Agent-Sandbox/awesome-templates//crush --sandbox-timeout 1800 --yes
export SANDBOX_ID='<sandbox-id-returned-by-launch>'
abx sandbox command list "$SANDBOX_ID"
```

`--sandbox-timeout 1800` is the sandbox lifetime in seconds; `command_timeout`/`timeout_s` limits one task, while `ABX_HTTP_TIMEOUT`/SDK `timeout` controls client waiting. These are separate limits.

Launch starts this instance's application; do not create a second sandbox or second server. For OpenSandbox, follow its [setup](../docs/using-templates.md#cli-sdk-and-http) and set `ABX_PROVIDER=opensandbox`; the Python examples below read that same choice.

```bash
ABX_HTTP_TIMEOUT=420 abx run "$SANDBOX_ID" crush --json-args '{"prompt":"Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.","allow_tools":true,"cwd":"/home/user/app","command_timeout":300}'
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
            print(await client.commands.run('crush', prompt='Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.', allow_tools=True, cwd='/home/user/app', command_timeout=300))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

## Quick start (HTTP POST)

Use the [direct HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserving gateway headers, URL path/query and the independent application token. Send `POST /commands/crush` with `Content-Type: application/json` and this direct argument object, without an `args` wrapper:

```json
{
  "prompt": "Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.",
  "allow_tools": true,
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

| Command | Parameters | Result |
| --- | --- | --- |
| crush_version | none | actual pinned0.98.1 string |
| crush_setup_check | none | installed/version/api_key_set/base_url_set/model_set; read-only flags |
| crush | prompt:str required, nonempty/no NUL/max256KiB UTF-8; cwd:str="" existing inside WORKSPACE; allow_tools:bool=false; command_timeout:int=600,1..1800seconds | {stdout:str,stderr:str,exit_code:int} |

Named-command results are buffered rather than streamed. `cwd` must be an existing directory satisfying the template's path constraints. Editing/tool permission allows model actions with the sandbox user's authority. Client disconnect is not a cancellation mechanism.

## Configuration

| Name | Required | Default | Purpose |
| --- | --- | --- | --- |
| CRUSH_API_KEY | model calls | empty | explicit compatible-provider credential |
| CRUSH_BASE_URL | model calls | empty | HTTP(S) endpoint; no userinfo/query/fragment |
| CRUSH_MODEL | model calls | empty | bounded native model identifier |
| WORKSPACE | no | /home/user/app | existing caller workspace |
| ABX_SERVER_TOKEN | yes | empty | Export an independent application token before the template launch; separate from model and gateway credentials |

Private HOME/XDG/CRUSH config/data and correct native disable-default-providers/auto-update flags prevent loading caller global state. Existing .crushrc/crushrc/.crush.json/crush.json between cwd and the nearest Git worktree root are refused before a native run, because upstream automatically loads them. Caller configuration is preserved. With no Git root, upstream checks cwd only. Only PATH/optional CA settings plus private runtime settings enter children; cloud/GitHub/server keys are excluded. The selected key/base URL enter the private0600 config, are never prompt argv, and exact values are redacted from returned diagnostics. Project output can still contain project secrets.

## Resources

2 vCPU, 2048 MB RAM, application port 9000, non-root `user`. Working directory: `/home/user/app`. Disk capacity and lifetime depend on the selected platform. Model tasks require outbound access to the configured model service and incur that service's charges.

## Contributing

To develop the template, read [CONTRIBUTING](../CONTRIBUTING.md) and the [design](../docs/design/crush.md).

## Issues

[Template Issue65](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/65); [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues), [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).

## License

Template wrapper code is [Apache-2.0](../LICENSE). Crush0.98.1 is **FSL-1.1-MIT**, not currently MIT or an OSI-approved open-source release. Preserve and review the exact [upstream license](upstream-LICENSE.md), future-license date and restrictions; do not infer unrestricted commercial redistribution. The unmodified official binary and all bundled notices are installed intact; model weights are not included.
