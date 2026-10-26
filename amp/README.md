# amp

Sourcegraph Amp CLI in an Agent Sandbox. The image pins `@ampcode/cli` and serves named commands on port 9000.

## What it does

Installs the Amp CLI (`amp`) and registers four commands:

| Command | What it runs |
|---|---|
| `amp_version` | `amp version` |
| `amp_setup_check` | `amp version`, then reads existing settings without changing them |
| `amp_execute` | `amp --no-color --no-notifications --no-ide -x <prompt>` |

`amp_execute` adds `--stream-json` when `stream_json` is true. The HTTP response is the full stdout after the process exits. It is not a live stream.

`amp_execute` checks `AMP_API_KEY` before it starts the CLI. If the variable is missing or blank, the command returns an error that names `AMP_API_KEY` and says the CLI would otherwise start a device-login flow.

Amp does not accept a DashScope key, `ABX_LLM_API_KEY`, or an OpenAI-compatible base URL. The token is an Amp access token from [ampcode.com settings](https://ampcode.com/settings/security#access-token).

`--dangerously-allow-all` is a flag the `0.0.1792022479-ge66e24` binary accepts. `amp --help` on that version does not list it in the options section. The help text documents the settings key `amp.dangerouslyAllowAll`. `amp_execute` adds that flag only when `dangerously_allow_all=true` is explicitly requested. Existing caller-owned settings remain unchanged; inspect their effective permission flag with `amp_setup_check`. The image default is false.

## Stack

The default recipe uses the Alibaba FC generation-2 base, non-root `user`, and the published `agent-sandbox-server==0.4.0a6` package.

Official `@ampcode/cli@0.0.1792022479-ge66e24` Linux x86_64 CLI, platform Node.js 20, Git and ripgrep.

[Dockerfile](Dockerfile) · [template.yaml](template.yaml)

## Problem solved

Use an installed tool in an isolated sandbox, submit work through CLI, Python or HTTP, then export the files. Configure model and cloud-sandbox credentials separately.

## Quick start (CLI)

Install the CLI/Python client and configure your platform (Sandbox API key, connection address and build image registry) using the [usage guide](../docs/using-templates.md#installation), then set the separate model/application credentials below. Launching the public recipe does not require a repository checkout.

Obtain an Amp account key using [Amp authentication](https://ampcode.com/docs/cli). Named commands use `AMP_API_KEY` and do not start browser login. The model and backend are selected by Amp; this wrapper does not accept a custom OpenAI endpoint/model. `AMP_URL` is an Amp service address, not an LLM API base.

Replace every `<...>` placeholder with your own value; use an exact model ID available to your account. Set secrets in your own terminal or secret manager, never in the image, YAML or public logs. Configure these variables **before** launch; later host changes do not reconfigure the running application.

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export AMP_API_KEY='<your-model-or-vendor-key>'
abx template launch Alibaba-Agent-Sandbox/awesome-templates//amp --sandbox-timeout 1800 --yes
export SANDBOX_ID='<sandbox-id-returned-by-launch>'
abx sandbox command list "$SANDBOX_ID"
```

`--sandbox-timeout 1800` is the sandbox lifetime in seconds; `command_timeout`/`timeout_s` limits one task, while `ABX_HTTP_TIMEOUT`/SDK `timeout` controls client waiting. These are separate limits.

Launch starts this instance's application; do not create a second sandbox or second server. For OpenSandbox, follow its [setup](../docs/using-templates.md#cli-sdk-and-http) and set `ABX_PROVIDER=opensandbox`; the Python examples below read that same choice.

```bash
ABX_HTTP_TIMEOUT=720 abx run "$SANDBOX_ID" amp_execute --json-args '{"prompt":"Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.","dangerously_allow_all":true}'
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
            9000, token=os.environ["ABX_SERVER_TOKEN"], timeout=720
        )
        try:
            print(await client.commands.run('amp_execute', prompt='Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.', dangerously_allow_all=True))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

## Quick start (HTTP POST)

Use the [direct HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserving gateway headers, URL path/query and the independent application token. Send `POST /commands/amp_execute` with `Content-Type: application/json` and this direct argument object, without an `args` wrapper:

```json
{
  "prompt": "Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.",
  "dangerously_allow_all": true
}
```

The response is `{"result": ...}`; see the command reference for its actual content type. Model text varies. Set the HTTP wait to at least 720 seconds; the command execution deadline is separate, and disconnecting does not guarantee remote cancellation. Authentication failures return 401, invalid argument types 400, and execution errors an error response. If a result includes `exit_code`, also check that it is zero.

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

| Command | Parameters | Returns | Description |
|---|---|---|---|
| `amp_version` | none | string | First token of `amp version`, for example `0.0.1792022479-ge66e24`. |
| `amp_setup_check` | none | object | `installed`, `package`, `version`, `api_key_set`, `settings_path`, `settings_exists`, `dangerously_allow_all`, `updates_mode`. No files are written. An absent file reports false and `default`. |
| `amp_execute` | `prompt` string, required. `stream_json` boolean, optional, default `false`; `dangerously_allow_all` boolean, optional, default `false`. | string | Stdout of `amp -x`. `--stream-json` when `stream_json` is true. |

Named-command results are buffered rather than streamed. `cwd` must be an existing directory satisfying the template's path constraints. Editing/tool permission allows model actions with the sandbox user's authority. Client disconnect is not a cancellation mechanism.

## Configuration

This subprocess lifecycle requires Linux. The command closes its owned process group on success and error as well as at the deadline. It drains both output pipes while keeping the leader unreaped until group cleanup, so redirected background descendants cannot outlive a completed command.

| Name | Required | Default | Purpose |
|---|---|---|---|
| `AMP_API_KEY` | for `amp_execute` | empty | Amp access token. Not a DashScope or OpenAI key. Declared empty in `template.yaml`. |
| `AMP_URL` | no | `https://ampcode.com/` | Amp service URL. The CLI's own default. Not set by the image. |
| `AMP_SETTINGS_FILE` | no | `/home/user/.config/amp/settings.json` in the image | Caller-owned settings file inspected without writes. |
| `AMP_LOG_FILE` | no | `/home/user/.cache/amp/logs/cli.log` in the image | CLI log path. |
| `ABX_SERVER_TOKEN` | yes | empty | Export an independent application token before the template launch; separate from model and gateway credentials |

Before `template launch`, securely export the secret variables declared empty in the manifest so the application reads them at startup. Keep values out of images, YAML and logs.


## Resources

2 vCPU, 2048 MB RAM, application port 9000, non-root `user`. Working directory: `/home/user/app`. Disk capacity and lifetime depend on the selected platform. Model tasks require outbound access to the configured model service and incur that service's charges.

## Contributing

To develop the template, read [CONTRIBUTING](../CONTRIBUTING.md) and the [design](../docs/design/amp.md).

## Issues

| Topic | Repository |
|---|---|
| This template, the spec, the checker | [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues) |
| Python SDK or `agent-sandbox-server` | [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), title prefix `[templates]` |
| `abx` CLI | [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues), title prefix `[templates]` |

## License

Apache-2.0, the same license as this repository. See [LICENSE](../LICENSE).
