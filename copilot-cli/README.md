# Copilot CLI

[中文](README.zh-CN.md).

## What it does

Runs the genuine pinned GitHub Copilot CLI with an explicit OpenAI-compatible BYOK endpoint. Each prompt uses private temporary state. File editing requires `allow_write=true`; shell execution, delegation and web tools are absent from the fixed model tool list.

## Stack

The default recipe uses the Alibaba FC generation-2 base, non-root `user`, and the published `agent-sandbox-server==0.4.0a6` package.

Original `@github/copilot@1.0.100` with the matching Linux x86_64 native package.

[Dockerfile](Dockerfile) · [template.yaml](template.yaml) · [upstream license](UPSTREAM-LICENSE.md)

## Problem solved

Use an installed tool in an isolated sandbox, submit work through CLI, Python or HTTP, then export the files. Configure model and cloud-sandbox credentials separately.

## Quick start (CLI)

Install the CLI/Python client and configure your platform (Sandbox API key, connection address and build image registry) using the [usage guide](../docs/using-templates.md#installation), then set the separate model/application credentials below. Launching the public recipe does not require a repository checkout.

This template uses Copilot CLI's BYOK Chat Completions mode, not a GitHub-hosted Copilot model. Supply the three `COPILOT_*` settings; no GitHub login or token is required by this path. The example explicitly permits project writes with `allow_write=true`.

For the DashScope base below, create a Beijing-region key following [Model Studio API-key setup](https://www.alibabacloud.com/help/en/model-studio/get-api-key) and use a model allowed for that account. Other regions and Coding Plans use their matching keys/endpoints.

Replace every `<...>` placeholder with your own value; use an exact model ID available to your account. Set secrets in your own terminal or secret manager, never in the image, YAML or public logs. Configure these variables **before** launch; later host changes do not reconfigure the running application.

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export COPILOT_PROVIDER_API_KEY='<your-model-or-vendor-key>'
export COPILOT_PROVIDER_BASE_URL='https://dashscope.aliyuncs.com/compatible-mode/v1'
export COPILOT_MODEL='<model-id-from-your-provider>'
abx template launch Alibaba-Agent-Sandbox/awesome-templates//copilot-cli --sandbox-timeout 1800 --yes
export SANDBOX_ID='<sandbox-id-returned-by-launch>'
abx sandbox command list "$SANDBOX_ID"
```

`--sandbox-timeout 1800` is the sandbox lifetime in seconds; `command_timeout`/`timeout_s` limits one task, while `ABX_HTTP_TIMEOUT`/SDK `timeout` controls client waiting. These are separate limits.

Launch starts this instance's application; do not create a second sandbox or second server. For OpenSandbox, follow its [setup](../docs/using-templates.md#cli-sdk-and-http) and set `ABX_PROVIDER=opensandbox`; the Python examples below read that same choice.

```bash
ABX_HTTP_TIMEOUT=420 abx run "$SANDBOX_ID" copilot --json-args '{"prompt":"Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.","allow_write":true,"cwd":"/home/user/app","command_timeout":300}'
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
            print(await client.commands.run('copilot', prompt='Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.', allow_write=True, cwd='/home/user/app', command_timeout=300))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

## Quick start (HTTP POST)

Use the [direct HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserving gateway headers, URL path/query and the independent application token. Send `POST /commands/copilot` with `Content-Type: application/json` and this direct argument object, without an `args` wrapper:

```json
{
  "prompt": "Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.",
  "allow_write": true,
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
| copilot_version | none | `{native_version:"1.0.100"}`, actual binary check; no model key |
| copilot_setup_check | none | mode, base_url_set/api_key_set/model_set booleans, github_auth_required=false; no network |
| copilot | prompt:str required,1..32768UTF-8 bytes/no NUL; cwd:str="", existing directory inside WORKSPACE after symlink resolution; allow_write:bool=false; command_timeout:int=300,1..600seconds | stdout:str, stderr:str, exit_code:int, native_version:str |

Named-command results are buffered rather than streamed. `cwd` must be an existing directory satisfying the template's path constraints. Editing/tool permission allows model actions with the sandbox user's authority. Client disconnect is not a cancellation mechanism.

## Configuration

| Name | Required/default | Meaning |
| --- | --- | --- |
| COPILOT_PROVIDER_BASE_URL | model calls/empty | HTTPS, or loopback HTTP for local development; no userinfo/query/fragment; max2048characters |
| COPILOT_PROVIDER_API_KEY | model calls/empty | explicit endpoint credential, max8192characters/no CR/LF/NUL |
| COPILOT_MODEL | model calls/empty | explicit model identifier, max200ASCII characters |
| WORKSPACE | /home/user/app | allowed cwd root |
| ABX_SERVER_TOKEN | required; empty declaration | Export an independent application token before the template launch; separate from model and gateway credentials |

The three model settings are captured at server startup. BYOK type=openai, wire API=completions and transport=http are fixed; token limits65536prompt/4096output. No key-command, extra headers, bearer override, GitHub token or unrelated host credential is forwarded. Native secret-env filtering and wrapper redaction mask the exact key. Only PATH/optional CA paths plus private HOME/XDG/temp/state enter the process. Private profile/cache/log state is removed after identity-pinned process group and marked detached descendants stop; project edits remain. The owned cloud sandbox is the final boundary against malicious code. See [runtime environment](../docs/runtime-environment.md) and [official BYOK](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/use-byok-models).

## Resources

2 vCPU, 2048 MB RAM, application port 9000, non-root `user`. Working directory: `/home/user/app`. Disk capacity and lifetime depend on the selected platform. Model tasks require outbound access to the configured model service and incur that service's charges.

## Contributing

To develop the template, read [CONTRIBUTING](../CONTRIBUTING.md) and the [design](../docs/design/copilot-cli.md).

## Issues

[Issue64](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/64). Missing accounts/model support stay explicit; never substitute an unrelated credential.

SDK/server bugs: [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues). CLI bugs: [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).

## License

Wrapper source: Apache-2.0, [repository license](../LICENSE). The unmodified native GitHub Copilot CLI is under its own [license](UPSTREAM-LICENSE.md), retained in the image and installed package. Its redistribution conditions require an application/service providing material functionality beyond the CLI and prohibit standalone/primary-product redistribution. The authenticated remote API/file-transfer/sandbox service is independently licensed; this template does not relicense the CLI or grant GitHub service access.
