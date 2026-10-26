# OpenCode sandbox

[中文](README.zh-CN.md)

Run OpenCode coding tasks in an isolated workspace, call them through CLI/Python/HTTP, and download the generated files.

## What it does

`opencode_run` asks the installed OpenCode CLI to edit, create or refactor files without an interactive terminal. It returns text, JSON events and a session ID. Reuse that exact ID to continue a task. The optional `opencode_serve_start` command starts OpenCode's own HTTP service; ordinary coding tasks do not need it.

## Stack

- OpenCode `opencode-ai@1.19.0`, Git and ripgrep.
- Python 3.13, Node.js 20 and Bash from the platform base image.
- Template application on port 9000; optional OpenCode service on port 4096.
- Non-root `user`; application files at `/home/user/app`, task files in the workspace you create.

## Problem solved

Use this template to let an agent modify an existing project or generate runnable files without installing the CLI on your machine. The examples create `hello.py` in `/home/user/workspace`, run it, then export the file before deleting the sandbox.

## Quick start (CLI)

Install the published tools and configure your sandbox platform using the [installation guide](../docs/using-templates.md#installation). Express source preparation requires Docker, ACR and the documented platform credentials. Model credentials are separate from that platform account.

Configure the application **before launching**. This example uses the mainland DashScope OpenAI-compatible endpoint. Use a model API key accepted by that endpoint; a sandbox API key is not a model key.

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="<independent-application-token>"
export ABX_LLM_API_KEY="<model-api-key>"
export ABX_LLM_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
export ABX_HTTP_TIMEOUT=660
abx template launch Alibaba-Agent-Sandbox/awesome-templates//opencode --sandbox-timeout 1800 --yes
```

Replace the next placeholder with the sandbox ID returned by launch. For OpenSandbox, configure its provider first and use `ABX_PROVIDER=opensandbox` consistently in every example.

```bash
export ABX_SANDBOX_ID="<returned-sandbox-id>"
abx exec "$ABX_SANDBOX_ID" -- mkdir -p /home/user/workspace
abx run "$ABX_SANDBOX_ID" opencode_version
abx run "$ABX_SANDBOX_ID" opencode_setup_check
abx run "$ABX_SANDBOX_ID" opencode_run --json-args '{"prompt":"Create hello.py in the current directory that prints Hello from OpenCode, then run it.","model":"dashscope/qwen3.8-flash","cwd":"/home/user/workspace"}'
abx download "$ABX_SANDBOX_ID" /home/user/workspace/hello.py ./hello.py
```

The task returns an object with `text`, `stdout`, `session_id`, `model`, `agent` and `cwd`. Text varies with the model; the downloaded Python file should print `Hello from OpenCode` when run. Choose CLI, SDK or HTTP below as alternatives for the same task, rather than creating three sandboxes.

## Quick start (Python SDK)

Install `agent-sandbox-client==0.4.0a6` in your virtual environment. Keep the variables above and connect to the **already launched** application. Save this complete example as `quickstart.py`:

```python
import asyncio
import os
from pathlib import Path
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.connect(
        os.environ["ABX_SANDBOX_ID"], provider=os.environ["ABX_PROVIDER"]
    )
    try:
        await sb.commands.run("mkdir -p /home/user/workspace")
        client = await sb.application_client(
            9000, token=os.environ["ABX_SERVER_TOKEN"], timeout=660
        )
        try:
            result = await client.commands.run(
                "opencode_run",
                prompt="Create hello.py in the current directory that prints Hello from OpenCode, then run it.",
                model="dashscope/qwen3.8-flash",
                cwd="/home/user/workspace",
            )
            print(result["text"])
            Path("hello.py").write_bytes(
                await sb.files.read_bytes("/home/user/workspace/hello.py")
            )
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

Run `python quickstart.py`. Closing these clients does not delete the sandbox; perform the cleanup below after exporting the files you need. `sb.commands.run` executes a process, whereas `client.commands.run` calls a registered template command.

## Quick start (HTTP POST)

Set `Content-Type: application/json`.

Use `POST /commands/opencode_run` with this direct JSON body (not an extra `arguments` wrapper):

```json
{"prompt":"Create hello.py in the current directory that prints Hello from OpenCode, then run it.","model":"dashscope/qwen3.8-flash","cwd":"/home/user/workspace"}
```

The [complete HTTP calling example](../docs/using-templates.md#cli-sdk-and-http) resolves the provider URL and gateway headers, then sends the application token. Keep the returned gateway path/query and existing headers; change its command path to `/commands/opencode_run`, body to the object above and `httpx.AsyncClient(timeout=660)`. Prepare the workspace with the CLI command above first.

The response is `{"result": {"text": "...", "stdout": "...", "session_id": "...", "model": "dashscope/qwen3.8-flash", "agent": "", "cwd": "/home/user/workspace"}}`. It is buffered JSON, not a token stream. Invalid arguments, failed authentication and command failures remain errors. A disconnected HTTP client does not guarantee cancellation of the model process.

## Command reference

| Command | Parameters | Returns | Upstream |
|---|---|---|---|
| `opencode_run` | see the table below | object | `opencode run --pure --format json --auto ...` |
| `opencode_version` | none | `"1.19.0"` | `opencode --version` |
| `opencode_setup_check` | none | `"ok"` | `opencode --version` plus a read of `opencode.json` |
| `opencode_serve_start` | `port` integer, default `4096`; `hostname` string, default `0.0.0.0` | object | `opencode serve --pure --hostname --port` |
| `opencode_serve_status` | none | object | localhost `GET /global/health` |
| `opencode_serve_stop` | none | `"stopped"` | `SIGTERM` to the process this template started |

`opencode_run` parameters:

| Parameter | Type | Required | Default | Meaning |
|---|---|---|---|---|
| `prompt` | string | yes | | Positional argv after `--`; never interpolated into a shell string. |
| `model` | string | no | `OPENCODE_MODEL`, else `dashscope/qwen3.8-flash` | `--model`, form `provider/model`. |
| `agent` | string | no | empty (CLI primary agent, `build`) | `--agent` when non-empty. |
| `session` | string | no | empty | `--session` to continue that session id. |
| `continue_session` | boolean | no | `false` | `--continue` (last session). Pass a JSON boolean. |
| `cwd` | string | no | `/home/user/app` (the module directory for local runs) | `--dir` and the child working directory. Must be an existing directory. |

`opencode_run` returns:

| Field | Meaning |
|---|---|
| `text` | Concatenated `type: text` parts from the JSON events. |
| `stdout` | JSON events with secret environment values redacted, one event per line. |
| `session_id` | `sessionID` from those events, or empty. |
| `model` | Selector that was passed to `--model`. |
| `agent` | Agent name that was passed, or empty. |
| `cwd` | Directory that was passed to `--dir`. |

A missing `prompt` is HTTP 400. A non-zero CLI exit is HTTP 500 `{"error","type":"RuntimeError"}`. CLI error output is omitted, so prompts, tool arguments, and credentials are not copied into error messages. Successful event values redact known environment secrets. Serve logs are discarded. Timeout is 600 seconds. Stdin is `/dev/null`.

`opencode_serve_start` returns `running`, `port`, `hostname`, `pid`, `healthy`, and `version`. It waits until `GET http://127.0.0.1:<port>/global/health` returns `{"healthy": true, "version": "1.19.0"}`. The target-side health probe supports `OPENCODE_SERVER_PASSWORD` and requires the pinned version. Resolve the public endpoint and gateway headers with `await sb.network.resolve(port)`; the localhost address is internal. A second start with the same port and hostname returns the current status. Start/status/stop are serialized by an in-process lock. Stop signals only the Popen child owned by this interpreter and verifies its process group; old PID files are never read. Restarting the command server does not adopt an older serve process; recycle the sandbox to clean up such a process.

## Configuration

| Setting | Required / default | How to use it |
|---|---|---|
| `ABX_LLM_API_KEY` | Required for `dashscope/*` model calls | Export on your machine before launch; the template reads it in the application process. |
| `ABX_LLM_BASE_URL` | Required for `dashscope/*` | Full OpenAI-compatible endpoint, including `/v1`; example above. Match the key and service region/account. |
| `model` command argument | Optional; default `dashscope/qwen3.8-flash` | Pass `dashscope/<model-id>` to select a model available at your endpoint. The wrapper adds a missing DashScope model ID to its child configuration for that call. |
| `ABX_SERVER_TOKEN` | Required before source launch | Independent application access token, reused by CLI/SDK/HTTP callers. |
| `OPENCODE_API_KEY` | Only for an `opencode/*` Zen model | Provider-specific model credential; does not replace DashScope credentials. |
| `OPENCODE_SERVER_PASSWORD` | Optional | Basic-auth password for the optional `opencode serve` API. Set before launch if you expose that service. |
| `ABX_HTTP_TIMEOUT` | Example: 660 seconds | CLI HTTP wait; the coding subprocess itself has a 600-second deadline. SDK/HTTP callers set their own wait. |

**Login:** the DashScope example uses an API key, not interactive login. Your local OpenCode login/configuration is not copied into the sandbox. The template's `/home/user/app/opencode.json` already maps its `dashscope` provider to `ABX_LLM_BASE_URL` and `ABX_LLM_API_KEY`; no image edit or `opencode auth login` is needed for this path. OpenCode-native settings use `~/.config/opencode`, and native authentication/session state uses `~/.local/share/opencode`; these are separate from the sandbox-platform account.

**Another endpoint or model:** keep the `dashscope/` prefix for this custom compatible-provider configuration, change `ABX_LLM_BASE_URL` before launching and pass the desired model ID as the command's `model`. Check that your service accepts both the key and model; a model name in an example is not an account entitlement. This template pins `OPENCODE_MODEL` in its manifest, so exporting a different host value does not override that default in CLI 0.5.6; use the command argument instead.

**Another upstream provider:** native OpenCode supports other provider configurations, but the template does not translate every credential into `ABX_LLM_*`. Preserve its existing DashScope configuration and add the provider-specific configuration using [OpenCode's config documentation](https://opencode.ai/docs/config/) and [provider documentation](https://opencode.ai/docs/providers/), then select `provider/model`. Files or login state must be provisioned inside this sandbox; do not assume the host's credentials are inherited. Model APIs that are not OpenAI-compatible need their own supported provider configuration.

Changing local exports after launch does not reconfigure the existing application. Launch a new instance with the intended model settings. Do not start a second template command server.

## Resources

The manifest requests 2 vCPU and 2048 MB RAM. Disk capacity and maximum lifetime depend on the selected platform. The model service requires outbound connectivity and may incur its own charges. Port 4096 is used only after `opencode_serve_start`; resolve it through the provider and keep both gateway and OpenCode authentication.

The wrapper automatically approves OpenCode tool execution (`--auto`). Its `cwd` selects the project directory, not a filesystem permission boundary: the model can execute commands and modify files writable by `user`. Provide only the credentials and files needed for this task.

OpenCode runs in the command's `cwd`. The example explicitly creates a workspace instead of editing template application files. Export code, session data and other required output before deleting the sandbox; changes do not update the original template.

```bash
abx kill "$ABX_SANDBOX_ID"
```

The owner should also delete the exact prepared template/image identified in launch output when no longer needed; follow [resource cleanup](../docs/using-templates.md#cli-sdk-and-http). No key or login state should be baked into a reusable image.

## Contributing

For template authoring, see [CONTRIBUTING](../CONTRIBUTING.md) and the [OpenCode design](../docs/design/opencode.md).

## Issues

Report template behavior to [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues), client/server issues to [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), and CLI issues to [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Redact keys and private project data.

## License

Apache-2.0; see [LICENSE](../LICENSE). OpenCode is installed from the pinned upstream package and retains its own upstream license.
