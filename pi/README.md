# Pi

## What it does

Run the official [Pi coding CLI](https://github.com/earendil-works/pi) in Alibaba's sandbox base image. This template exposes one ephemeral print-mode task against an OpenAI-compatible model endpoint. It is an independent template, with no E2B template registration dependency.

## Stack

The default recipe uses the Alibaba FC generation-2 base, non-root `user`, and the published `agent-sandbox-server==0.4.0a6` package.

Official `@earendil-works/pi-coding-agent@1.3.0`, Node.js `24.16.0`, fd `10.5.0` and ripgrep `15.2.0`.

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
export PI_API_KEY='<your-model-or-vendor-key>'
export PI_BASE_URL='https://dashscope.aliyuncs.com/compatible-mode/v1'
export PI_MODEL='<model-id-from-your-provider>'
abx template launch Alibaba-Agent-Sandbox/awesome-templates//pi --sandbox-timeout 1800 --yes
export SANDBOX_ID='<sandbox-id-returned-by-launch>'
abx sandbox command list "$SANDBOX_ID"
```

`--sandbox-timeout 1800` is the sandbox lifetime in seconds; `command_timeout`/`timeout_s` limits one task, while `ABX_HTTP_TIMEOUT`/SDK `timeout` controls client waiting. These are separate limits.

Launch starts this instance's application; do not create a second sandbox or second server. For OpenSandbox, follow its [setup](../docs/using-templates.md#cli-sdk-and-http) and set `ABX_PROVIDER=opensandbox`; the Python examples below read that same choice.

```bash
ABX_HTTP_TIMEOUT=420 abx run "$SANDBOX_ID" pi --json-args '{"prompt":"Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.","allow_tools":true,"cwd":"/home/user/app","command_timeout":300}'
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
            print(await client.commands.run('pi', prompt='Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.', allow_tools=True, cwd='/home/user/app', command_timeout=300))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

## Quick start (HTTP POST)

Use the [direct HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserving gateway headers, URL path/query and the independent application token. Send `POST /commands/pi` with `Content-Type: application/json` and this direct argument object, without an `args` wrapper:

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
|---|---|---|
| pi_version | none | Installed version string. |
| pi_tools_check | none | Actually execute official read/find/grep/ls offline on disposable files; returns `read/find/grep/ls OK`. |
| pi_setup_check | none | Installed/version/pin, boolean key/endpoint/model presence, workspace. No credentials or endpoint value. |
| pi | prompt: string required; cwd: string = ""; allow_tools: boolean = false; command_timeout: integer = 600 | Buffered, credential-redacted text. Deadline 1–1800 seconds. |

Named-command results are buffered rather than streamed. `cwd` must be an existing directory satisfying the template's path constraints. Editing/tool permission allows model actions with the sandbox user's authority. Client disconnect is not a cancellation mechanism.

## Configuration

Set `PI_BASE_URL` to a compatible chat-completions endpoint, `PI_MODEL` to its model ID, and `PI_API_KEY` to its key. All three are required. URLs with embedded credentials, query strings or fragments are refused. No interactive login occurs. Key names in metadata have empty values.

Each task creates a private temporary `models.json` using upstream's `$PI_API_KEY` interpolation, and removes that directory after success, failure or cancellation. User configuration and sessions are not reused. `--offline` disables automatic catalog/startup network traffic; the requested model call still uses the endpoint. Extensions, MCP, skills, context files, themes and prompt templates are disabled.

The image explicitly provides pinned `fd` and `rg`; offline mode therefore needs no runtime tool download. `pi_tools_check` runs all four default tool implementations without a model, and is part of the image/provider smoke.

The default tools are exactly `read,grep,find,ls`. `allow_tools=true` explicitly adds `edit,write,bash`, granting the model permission to change and execute code throughout this sandbox user's accessible files. Pi's `--no-approve` ignores trust-gated project configuration; it does not restrict tools. The tool allowlist controls this wrapper's default behavior; the sandbox remains the isolation boundary. Do not expose writable model execution to untrusted callers.

On Linux, the wrapper owns a new process group, drains both output streams and stops that group before reaping its leader on success, error, deadline or Python cancellation. Children that deliberately create a new session escape this process-group boundary. Disconnecting an HTTP client is not a cancellation API.

## Resources

2 vCPU, 2048 MB RAM, application port 9000, non-root `user`. Working directory: `/home/user/app`. Disk capacity and lifetime depend on the selected platform. Model tasks require outbound access to the configured model service and incur that service's charges.

## Contributing

To develop the template, read [CONTRIBUTING](../CONTRIBUTING.md) and the [design](../docs/design/pi.md).

## Issues

[Template Issue 41](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/41). File server/client defects in [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), and CLI defects in [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Include sanitized versions and reproduction steps.

## License

Apache-2.0 template code; upstream Pi is MIT. Official fd archives retain LICENSE-MIT and LICENSE-APACHE; ripgrep archives retain LICENSE-MIT, UNLICENSE and COPYING (MIT/Unlicense). Complete extracted release directories remain under `/opt/pi-tools/`; npm dependencies retain their license files. [LICENSE](../LICENSE).
