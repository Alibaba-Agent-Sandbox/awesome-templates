# Aider

## What it does

Runs the official `aider-chat==0.86.2` CLI against an explicitly selected git
working tree. The default is read-only **ask** mode. `allow_write=true` permits
whole-file edits to explicitly listed source/artifact paths. The wrapper stages
only those files, runs Aider, checks the original files have not changed, then
copies back selected results. It never auto-commits.

## Stack

The default recipe uses the Alibaba FC generation-2 base, non-root `user`, and the published `agent-sandbox-server==0.4.0a6` package.

Official `aider-chat==0.86.2` in a separate Python `3.12.12` environment under `/opt/aider`; the server uses the platform Python.

[Dockerfile](Dockerfile) · [template.yaml](template.yaml)

## Problem solved

Use an installed tool in an isolated sandbox, submit work through CLI, Python or HTTP, then export the files. Configure model and cloud-sandbox credentials separately.

## Quick start (CLI)

Install the CLI/Python client and configure your platform (Sandbox API key, connection address and build image registry) using the [usage guide](../docs/using-templates.md#installation), then set the separate model/application credentials below. Launching the public recipe does not require a repository checkout.

This headless path uses the three explicit model settings below; it does not run browser/OAuth login. The endpoint must support OpenAI-compatible Chat Completions and accept this adapter's `enable_thinking=false` setting. Aider uses whole-file text edits here; native tool-calling support is not required. Obtain the key and exact model ID from that endpoint's provider; a cloud Sandbox API key is a different credential. The example below uses DashScope's public compatible base as an example: use a key and model authorized for that same region, or replace all three together.

For the DashScope base below, create a Beijing-region key following [Model Studio API-key setup](https://www.alibabacloud.com/help/en/model-studio/get-api-key) and use a model allowed for that account. Other regions and Coding Plans use their matching keys/endpoints.

Replace every `<...>` placeholder with your own value; use an exact model ID available to your account. Set secrets in your own terminal or secret manager, never in the image, YAML or public logs. Configure these variables **before** launch; later host changes do not reconfigure the running application.

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export AIDER_API_KEY='<your-model-or-vendor-key>'
export AIDER_BASE_URL='https://dashscope.aliyuncs.com/compatible-mode/v1'
export AIDER_MODEL='<model-id-from-your-provider>'
abx template launch Alibaba-Agent-Sandbox/awesome-templates//aider --sandbox-timeout 1800 --yes
export SANDBOX_ID='<sandbox-id-returned-by-launch>'
abx sandbox command list "$SANDBOX_ID"
```

`--sandbox-timeout 1800` is the sandbox lifetime in seconds; `command_timeout`/`timeout_s` limits one task, while `ABX_HTTP_TIMEOUT`/SDK `timeout` controls client waiting. These are separate limits.

Launch starts this instance's application; do not create a second sandbox or second server. For OpenSandbox, follow its [setup](../docs/using-templates.md#cli-sdk-and-http) and set `ABX_PROVIDER=opensandbox`; the Python examples below read that same choice.

```bash
abx exec "$SANDBOX_ID" -- git -C /home/user/app init -q
```

```bash
ABX_HTTP_TIMEOUT=420 abx run "$SANDBOX_ID" aider --json-args '{"prompt":"Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.","files":"[\"generated_hello.py\",\"GENERATED_REPORT.md\"]","allow_write":true,"cwd":"/home/user/app","command_timeout":300}'
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
        await sb.commands.run("git -C /home/user/app init -q")
        client = await sb.application_client(
            9000, token=os.environ["ABX_SERVER_TOKEN"], timeout=420
        )
        try:
            print(await client.commands.run('aider', prompt='Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.', files='["generated_hello.py","GENERATED_REPORT.md"]', allow_write=True, cwd='/home/user/app', command_timeout=300))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

## Quick start (HTTP POST)

Every entry requires a Git worktree. Before this request, run the `abx exec ... git ... init -q` preparation above.

Use the [direct HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserving gateway headers, URL path/query and the independent application token. Send `POST /commands/aider` with `Content-Type: application/json` and this direct argument object, without an `args` wrapper:

```json
{
  "prompt": "Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.",
  "files": "[\"generated_hello.py\",\"GENERATED_REPORT.md\"]",
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

| Command | Arguments | Result / upstream |
| --- | --- | --- |
| `aider_version` | none | string `aider 0.86.2`; executes `aider --version` |
| `aider_setup_check` | none | booleans for installed/configured/home-blocked, pin and workspace; no secret/endpoint values |
| `aider` | required `prompt: string` (1–100000 chars); `cwd: string=""`; `files: string="[]"` containing a JSON list of at most 32 relative paths; `allow_write: boolean=false`; `command_timeout: integer=600` (1–1800) | dictionary with redacted stdout/stderr, exit code and selected changed paths |

Named-command results are buffered rather than streamed. `cwd` must be an existing directory satisfying the template's path constraints. Editing/tool permission allows model actions with the sandbox user's authority. Client disconnect is not a cancellation mechanism.

## Configuration

| Name | Default / meaning |
| --- | --- |
| `AIDER_API_KEY` | empty; required compatible API credential |
| `AIDER_BASE_URL` | empty; required HTTP(S) endpoint, without embedded credentials/query/fragment |
| `AIDER_MODEL` | empty; required model ID, `openai/` prefix added for LiteLLM |
| `WORKSPACE` | `/home/user/app`; default working directory |
| `ABX_SERVER_TOKEN` | Export an independent application token before the template launch; separate from model and gateway credentials |

Export `AIDER_API_KEY`, `AIDER_BASE_URL`, `AIDER_MODEL` and the independent application token before `template launch`. This path starts the named server for the instance; no second port-9010 server is needed. Changing the host environment does not reconfigure an existing application; launch a new instance after changing configuration.

The compatible-model settings disable thinking with `extra_body.enable_thinking=false`.
Your model endpoint must accept this request parameter. Credentials are not written to stage
files. Model input still leaves the sandbox for your configured endpoint.

**Native-home limitation:** fixed upstream Aider and configargparse always search
native-home defaults before appending `--config` and `--env-file`; those flags
cannot promise complete isolation. The wrapper refuses existing native-home
`.aider.conf.yml`, `.env`, model-settings/metadata and OAuth-key files before launch.
It does not replace `HOME`, modify a shared profile or import project config.
`PYTHON_DOTENV_DISABLED=1` disables dotenv loading. Aider's own cache/install and
analytics-disabled state can remain in the dedicated sandbox's native `.aider`
until that sandbox is destroyed. Do not run real calls on a shared host home.

## Resources

2 vCPU, 2048 MB RAM, application port 9000, non-root `user`. Working directory: `/home/user/app`. Disk capacity and lifetime depend on the selected platform. Model tasks require outbound access to the configured model service and incur that service's charges.

## Contributing

To develop the template, read [CONTRIBUTING](../CONTRIBUTING.md) and the [design](../docs/design/aider.md).

## Issues

[Template issue 50](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/50).
SDK/server issues belong in [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues);
CLI deployment issues in [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).

## License

Template glue is Apache-2.0. [Aider](https://github.com/Aider-AI/aider) is Apache-2.0;
its installed dependencies and [python-build-standalone](https://github.com/astral-sh/python-build-standalone)
retain their respective notices. See [official installation](https://aider.chat/docs/install.html)
and [compatible API guidance](https://aider.chat/docs/llms/openai-compat.html).
