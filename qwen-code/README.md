# Qwen Code

[中文](README.zh-CN.md)

## What it does

Runs the pinned Qwen Code CLI as a non-interactive coding agent, with named HTTP commands for coding, installation diagnostics and Python execution.

## Stack

The default recipe uses the Alibaba FC generation-2 base, non-root `user`, and the published `agent-sandbox-server==0.4.0a6` package.

Official `@qwen-code/qwen-code@0.23.0` and Node.js `24.16.0`; the CLI needs no extra OpenAI/DashScope Python package.

[Dockerfile](Dockerfile) · [template.yaml](template.yaml)

## Problem solved

Use an installed tool in an isolated sandbox, submit work through CLI, Python or HTTP, then export the files. Configure model and cloud-sandbox credentials separately.

## Quick start (CLI)

Install the CLI/Python client and configure your platform (Sandbox API key, connection address and build image registry) using the [usage guide](../docs/using-templates.md#installation), then set the separate model/application credentials below. Launching the public recipe does not require a repository checkout.

This path selects OpenAI-compatible API-key authentication and disables interactive OAuth. Set OPENAI_API_KEY (or DASHSCOPE_API_KEY fallback), OPENAI_BASE_URL and OPENAI_MODEL before launch. The blank manifest slots admit these host settings. If base/model are omitted, the runtime preserves https://dashscope.aliyuncs.com/compatible-mode/v1 and qwen3-coder-plus. The key, endpoint region and model entitlement must match. A qwen model argument overrides the model for that call. Change startup settings by launching a new instance; no local source edit is needed.

For the optional DashScope default, create a Beijing-region key following [Model Studio API-key setup](https://www.alibabacloud.com/help/en/model-studio/get-api-key) and use a model allowed for that account. Other regions and Coding Plans use their matching keys/endpoints.

Replace every `<...>` placeholder with your own value; use an exact model ID available to your account. Set secrets in your own terminal or secret manager, never in the image, YAML or public logs. Configure these variables **before** launch; later host changes do not reconfigure the running application.

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export OPENAI_API_KEY='<your-model-or-vendor-key>'
export OPENAI_BASE_URL='<your-chat-completions-base-url>'
export OPENAI_MODEL='<model-id-from-your-provider>'
abx template launch Alibaba-Agent-Sandbox/awesome-templates//qwen-code --sandbox-timeout 1800 --yes
export SANDBOX_ID='<sandbox-id-returned-by-launch>'
abx sandbox command list "$SANDBOX_ID"
```

`--sandbox-timeout 1800` is the sandbox lifetime in seconds; `command_timeout`/`timeout_s` limits one task, while `ABX_HTTP_TIMEOUT`/SDK `timeout` controls client waiting. These are separate limits.

Launch starts this instance's application; do not create a second sandbox or second server. For OpenSandbox, follow its [setup](../docs/using-templates.md#cli-sdk-and-http) and set `ABX_PROVIDER=opensandbox`; the Python examples below read that same choice.

```bash
ABX_HTTP_TIMEOUT=420 abx run "$SANDBOX_ID" qwen --json-args '{"prompt":"Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.","yolo":true,"cwd":"/home/user/app","command_timeout":300}'
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
            print(await client.commands.run('qwen', prompt='Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.', yolo=True, cwd='/home/user/app', command_timeout=300))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

## Quick start (HTTP POST)

Use the [direct HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserving gateway headers, URL path/query and the independent application token. Send `POST /commands/qwen` with `Content-Type: application/json` and this direct argument object, without an `args` wrapper:

```json
{
  "prompt": "Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.",
  "yolo": true,
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

| Command | Parameters | Result / upstream |
| --- | --- | --- |
| `qwen` | `prompt: str` required, nonempty; `max_turns: int=100` (1–1000); `model: str=""` uses `OPENAI_MODEL`; `cwd: str=""` uses workspace; `command_timeout: int=600` (1–1800 seconds); `yolo: bool=false` | String from `qwen -p PROMPT --auth-type openai --output-format json --max-session-turns N --max-wall-time SECONDS --no-chat-recording`; adds `--model MODEL`, `--yolo` when supplied |
| `qwen_version` | None | Real `qwen --version` string, no key needed |
| `qwen_setup_check` | None | Object with installed/version, pin, key/model/base-url presence and settings-file existence/JSON validity; never returns settings values or writes files |
| `run` | `script: str="main.py"` | Python stdout; native command with 120-second deadline |

Named-command results are buffered rather than streamed. `cwd` must be an existing directory satisfying the template's path constraints. Editing/tool permission allows model actions with the sandbox user's authority. Client disconnect is not a cancellation mechanism.

## Configuration

| Variable | Meaning |
| --- | --- |
| `OPENAI_API_KEY` | Primary model key for coding tasks; version/setup checks do not require it |
| `DASHSCOPE_API_KEY` | Fallback model key when `OPENAI_API_KEY` is empty; mapped only in the child process |
| `OPENAI_BASE_URL` | Default `https://dashscope.aliyuncs.com/compatible-mode/v1`; export before launch for another compatible endpoint |
| `OPENAI_MODEL` | Default `qwen3-coder-plus`; startup export or explicit command `model` wins |
| `WORKSPACE` | Default `/home/user/app` |
| `ABX_SERVER_TOKEN` | Required before template launch; independent of model and gateway credentials |

Diagnostics inspect `~/.qwen/settings.json` and `<workspace>/.qwen/settings.json` without altering contents or permissions. Normal upstream coding may maintain its own runtime cache. Upstream [model-provider configuration](https://github.com/QwenLM/qwen-code/blob/v0.23.0/docs/users/configuration/model-providers.md) and [headless usage](https://github.com/QwenLM/qwen-code/blob/v0.23.0/docs/users/features/headless.md) describe compatibility; confirm that your account and model support the required tool calling. Do not enable API logging with secrets in public artifacts.

## Resources

2 vCPU, 4096 MB RAM, application port 9000, non-root `user`. Working directory: `/home/user/app`. Disk capacity and lifetime depend on the selected platform. Model tasks require outbound access to the configured model service and incur that service's charges.

## Contributing

To develop the template, read [CONTRIBUTING](../CONTRIBUTING.md) and the [design](../docs/design/qwen-code.md).

## Issues

Track template work in [issue #26](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/26). File SDK/server bugs in [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues) and CLI bugs in [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Include sanitized commands, versions and actual failed gates.

## License

Apache-2.0 for this template. Qwen Code retains its [upstream license](https://github.com/QwenLM/qwen-code/blob/v0.23.0/LICENSE).
