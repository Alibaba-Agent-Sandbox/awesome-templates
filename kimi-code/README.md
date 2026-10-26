# kimi-code

## What it does

Run official Kimi Code 2.2.0 for one headless prompt in an existing sandbox directory. Each turn gets private temporary Kimi settings and cleans its owned process group. Upstream prompt mode automatically permits tools, so the wrapper requires explicit allow_tools=True before launching it. Results are buffered stream-JSON text; this template does not provide resumable sessions.

## Stack

The default recipe uses the Alibaba FC generation-2 base, non-root `user`, and the published `agent-sandbox-server==0.4.0a6` package.

Official Node CLI `@moonshot-ai/kimi-code@2.2.0` and Node.js `24.16.0`.

[Dockerfile](Dockerfile) · [template.yaml](template.yaml)

## Problem solved

Use an installed tool in an isolated sandbox, submit work through CLI, Python or HTTP, then export the files. Configure model and cloud-sandbox credentials separately.

## Quick start (CLI)

Install the CLI/Python client and configure your platform (Sandbox API key, connection address and build image registry) using the [usage guide](../docs/using-templates.md#installation), then set the separate model/application credentials below. Launching the public recipe does not require a repository checkout.

The default provider type is `openai`: use an authorized OpenAI-compatible base/key/model, without interactive Kimi login. The native CLI also supports its documented `kimi` and `anthropic` provider types, but changing the nonempty `KIMI_MODEL_PROVIDER_TYPE` manifest value requires your own source recipe; the base, model and key must all match that protocol.

For the DashScope base below, create a Beijing-region key following [Model Studio API-key setup](https://www.alibabacloud.com/help/en/model-studio/get-api-key) and use a model allowed for that account. Other regions and Coding Plans use their matching keys/endpoints.

Replace every `<...>` placeholder with your own value; use an exact model ID available to your account. Set secrets in your own terminal or secret manager, never in the image, YAML or public logs. Configure these variables **before** launch; later host changes do not reconfigure the running application.

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export KIMI_MODEL_API_KEY='<your-model-or-vendor-key>'
export KIMI_MODEL_BASE_URL='https://dashscope.aliyuncs.com/compatible-mode/v1'
export KIMI_MODEL_NAME='<model-id-from-your-provider>'
abx template launch Alibaba-Agent-Sandbox/awesome-templates//kimi-code --sandbox-timeout 1800 --yes
export SANDBOX_ID='<sandbox-id-returned-by-launch>'
abx sandbox command list "$SANDBOX_ID"
```

`--sandbox-timeout 1800` is the sandbox lifetime in seconds; `command_timeout`/`timeout_s` limits one task, while `ABX_HTTP_TIMEOUT`/SDK `timeout` controls client waiting. These are separate limits.

Launch starts this instance's application; do not create a second sandbox or second server. For OpenSandbox, follow its [setup](../docs/using-templates.md#cli-sdk-and-http) and set `ABX_PROVIDER=opensandbox`; the Python examples below read that same choice.

```bash
ABX_HTTP_TIMEOUT=420 abx run "$SANDBOX_ID" kimi --json-args '{"prompt":"Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.","allow_tools":true,"cwd":"/home/user/app","command_timeout":300}'
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
            print(await client.commands.run('kimi', prompt='Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.', allow_tools=True, cwd='/home/user/app', command_timeout=300))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

## Quick start (HTTP POST)

Use the [direct HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserving gateway headers, URL path/query and the independent application token. Send `POST /commands/kimi` with `Content-Type: application/json` and this direct argument object, without an `args` wrapper:

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

| Command | Parameters | Returns |
| --- | --- | --- |
| kimi_version | none | exact upstream version string |
| kimi_setup_check | none | installed/version/pinned_version, model/key/base flags and workspace; no credential values |
| kimi | prompt: required string, 1..65536 UTF-8 bytes; cwd: string, default configured workspace, must exist; command_timeout: integer, default 600, 1..1800 seconds; allow_tools: boolean, default false (must explicitly be true to launch upstream prompt mode) | buffered stream-JSON string; upstream nonzero exit, timeout or over-8-MiB output raises an error |

Named-command results are buffered rather than streamed. `cwd` must be an existing directory satisfying the template's path constraints. Editing/tool permission allows model actions with the sandbox user's authority. Client disconnect is not a cancellation mechanism.

## Configuration

| Variable | Required | Default / purpose |
| --- | --- | --- |
| KIMI_MODEL_NAME | for model turns | actual provider model ID |
| KIMI_MODEL_API_KEY | for model turns | empty secret declaration; inject at process start |
| KIMI_MODEL_BASE_URL | for model turns | explicit authorized compatible endpoint; no implicit credential forwarding |
| KIMI_MODEL_PROVIDER_TYPE | no | openai; also kimi or anthropic, matching upstream 2.2.0 |
| WORKSPACE | no | /home/user/app |
| ABX_SERVER_TOKEN | required; empty declaration | Export an independent application token before the template launch; separate from model and gateway credentials |

Model variables are verified in the actual npm 2.2.0 runtime and its official [provider documentation](https://github.com/MoonshotAI/kimi-code/blob/main/docs/en/configuration/providers.md). Each invocation sets KIMI_CODE_HOME to an owned temporary directory, leaving caller settings intact, and excludes unrelated cloud/registry credential variables. Secret values and JSON-escaped variants are redacted from returned stdout/stderr. The wrapper does not promise a read-only prompt mode.

## Resources

2 vCPU, 2048 MB RAM, application port 9000, non-root `user`. Working directory: `/home/user/app`. Disk capacity and lifetime depend on the selected platform. Model tasks require outbound access to the configured model service and incur that service's charges.

## Contributing

To develop the template, read [CONTRIBUTING](../CONTRIBUTING.md) and the [design](../docs/design/kimi-code.md).

## Issues

Template issues belong to [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/48); SDK/server to [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), CLI to [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Include versions and sanitized reproduction.

## License

Template wrapper: Apache-2.0, see [LICENSE](../LICENSE). Upstream Kimi Code: MIT, distributed through the pinned official npm package with its license retained.
