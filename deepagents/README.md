# DeepAgents

[中文](README.zh-CN.md).

## What it does

Runs actual DeepAgents0.7.25 with a local file/shell backend and explicit OpenAI-compatible chat model. Default requests expose zero tools. Explicit allow_tools=true enables exactly ls/read_file/write_file/edit_file/glob/grep/execute/delete. General-purpose and explicit subagents are disabled; task/delegation is absent.

## Stack

The default recipe uses the Alibaba FC generation-2 base, non-root `user`, and the published `agent-sandbox-server==0.4.0a6` package.

Official DeepAgents `0.7.25` and langchain-openai `1.7.2` in a hash-locked Python dependency environment.

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
export DEEPAGENTS_API_KEY='<your-model-or-vendor-key>'
export DEEPAGENTS_BASE_URL='https://dashscope.aliyuncs.com/compatible-mode/v1'
export DEEPAGENTS_MODEL='<model-id-from-your-provider>'
abx template launch Alibaba-Agent-Sandbox/awesome-templates//deepagents --sandbox-timeout 1800 --yes
export SANDBOX_ID='<sandbox-id-returned-by-launch>'
abx sandbox command list "$SANDBOX_ID"
```

`--sandbox-timeout 1800` is the sandbox lifetime in seconds; `command_timeout`/`timeout_s` limits one task, while `ABX_HTTP_TIMEOUT`/SDK `timeout` controls client waiting. These are separate limits.

Launch starts this instance's application; do not create a second sandbox or second server. For OpenSandbox, follow its [setup](../docs/using-templates.md#cli-sdk-and-http) and set `ABX_PROVIDER=opensandbox`; the Python examples below read that same choice.

```bash
ABX_HTTP_TIMEOUT=420 abx run "$SANDBOX_ID" deepagents --json-args '{"task":"Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.","allow_tools":true,"cwd":"/home/user/app","command_timeout":300}'
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
            print(await client.commands.run('deepagents', task='Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.', allow_tools=True, cwd='/home/user/app', command_timeout=300))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

## Quick start (HTTP POST)

Use the [direct HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserving gateway headers, URL path/query and the independent application token. Send `POST /commands/deepagents` with `Content-Type: application/json` and this direct argument object, without an `args` wrapper:

```json
{
  "task": "Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.",
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
| deepagents_version | none | actual installed0.7.25 |
| deepagents_setup_check | none | installed/version/api_key_set/base_url_set/model_set flags; read-only |
| deepagents | task:str required, nonempty/no NUL/max256KiB UTF-8; cwd:str="" existing inside WORKSPACE; allow_tools:bool=false; command_timeout:int=600,1..1800seconds | {stdout:str,stderr:str,exit_code:int} |

Named-command results are buffered rather than streamed. `cwd` must be an existing directory satisfying the template's path constraints. Editing/tool permission allows model actions with the sandbox user's authority. Client disconnect is not a cancellation mechanism.

## Configuration

| Name | Required | Default | Purpose |
| --- | --- | --- | --- |
| DEEPAGENTS_API_KEY | model calls | empty | explicit compatible-provider credential |
| DEEPAGENTS_BASE_URL | model calls | empty | HTTP(S), no userinfo/query/fragment |
| DEEPAGENTS_MODEL | model calls | empty | explicit model identifier |
| DEEPAGENTS_PYTHON | no | /opt/deepagents/bin/python | exact native dependency environment, version checked |
| WORKSPACE | no | /home/user/app | existing owned project directory |
| ABX_SERVER_TOKEN | yes | empty | Export an independent application token before the template launch; separate from model and gateway credentials |

The selected model settings remain in private stdin only, never inherited as environment by generated shells. Child runtime receives PATH/optional CA plus private HOME/XDG and disabled LangSmith tracing. LocalShellBackend gets only PATH/HOME/locale and the random non-secret process ownership marker, no inherited model/cloud/GitHub/server credentials. No skills/memory/profile files are loaded. The backend's virtual filesystem maps tool paths inside cwd; shell execution still has the sandbox user's full authority and is not restricted by that mapping.

## Resources

2 vCPU, 2048 MB RAM, application port 9000, non-root `user`. Working directory: `/home/user/app`. Disk capacity and lifetime depend on the selected platform. Model tasks require outbound access to the configured model service and incur that service's charges.

## Contributing

To develop the template, read [CONTRIBUTING](../CONTRIBUTING.md) and the [design](../docs/design/deepagents.md).

## Issues

[Issue67](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/67); template/catalog: [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues); SDK/server: [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues); CLI: [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).

## License

Template wrapper is [Apache-2.0](../LICENSE). DeepAgents and langchain-openai are MIT; preserve their unchanged [DeepAgents license](upstream-LICENSE) and [integration license](langchain-openai-LICENSE). Hash-locked third-party dependencies retain their own notices installed by pip; do not relabel all dependency code as Apache-2.0.
