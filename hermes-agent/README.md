# Hermes Agent

## What it does

Run the actual upstream Hermes Agent CLI with its local terminal and file toolsets. This template exposes the coding slice; messaging gateways, browser/desktop integrations and external terminal backends are not provisioned.

## Stack

The default recipe uses the Alibaba FC generation-2 base, non-root `user`, and the published `agent-sandbox-server==0.4.0a6` package.

NousResearch Hermes Agent `0.22.1` at commit `297552a9d646119871391d202509822cd86330df`, private Python `3.14.6`, and the upstream frozen dependency lock.

[Dockerfile](Dockerfile) · [template.yaml](template.yaml)

## Problem solved

Use an installed tool in an isolated sandbox, submit work through CLI, Python or HTTP, then export the files. Configure model and cloud-sandbox credentials separately.

## Quick start (CLI)

Install the CLI/Python client and configure your platform (Sandbox API key, connection address and build image registry) using the [usage guide](../docs/using-templates.md#installation), then set the separate model/application credentials below. Launching the public recipe does not require a repository checkout.

The default `openrouter` provider uses `OPENROUTER_API_KEY` and a model ID from your OpenRouter account. No interactive setup/login occurs. For a custom Chat-compatible service instead, export the declared `OPENAI_API_KEY` and `OPENAI_BASE_URL` before launch, and pass `provider="custom"` plus `model="<your-model-id>"` on every `hermes` call. `HERMES_PROVIDER` has a nonempty manifest default, so exporting that name alone does not switch the public recipe.

Replace every `<...>` placeholder with your own value; use an exact model ID available to your account. Set secrets in your own terminal or secret manager, never in the image, YAML or public logs. Configure these variables **before** launch; later host changes do not reconfigure the running application.

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export OPENROUTER_API_KEY='<your-model-or-vendor-key>'
export HERMES_MODEL='<model-id-from-your-provider>'
abx template launch Alibaba-Agent-Sandbox/awesome-templates//hermes-agent --sandbox-timeout 1800 --yes
export SANDBOX_ID='<sandbox-id-returned-by-launch>'
abx sandbox command list "$SANDBOX_ID"
```

`--sandbox-timeout 1800` is the sandbox lifetime in seconds; `command_timeout`/`timeout_s` limits one task, while `ABX_HTTP_TIMEOUT`/SDK `timeout` controls client waiting. These are separate limits.

Launch starts this instance's application; do not create a second sandbox or second server. For OpenSandbox, follow its [setup](../docs/using-templates.md#cli-sdk-and-http) and set `ABX_PROVIDER=opensandbox`; the Python examples below read that same choice.

```bash
ABX_HTTP_TIMEOUT=420 abx run "$SANDBOX_ID" hermes --json-args '{"prompt":"Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.","cwd":"/home/user/app","command_timeout":300}'
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
            print(await client.commands.run('hermes', prompt='Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.', cwd='/home/user/app', command_timeout=300))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

## Quick start (HTTP POST)

Use the [direct HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserving gateway headers, URL path/query and the independent application token. Send `POST /commands/hermes` with `Content-Type: application/json` and this direct argument object, without an `args` wrapper:

```json
{
  "prompt": "Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.",
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

| Parameter | Type | Required/default | Meaning |
|---|---|---|---|
| prompt | string | required | Task text; nonempty. |
| model | string | "" | Required argument or HERMES_MODEL; no implicit model choice. |
| provider | string | "" | Argument or HERMES_PROVIDER=openrouter; openrouter / openai-api / custom. |
| cwd | string | "" | Existing directory; relative to WORKSPACE. |
| max_turns | integer | 20 | Maximum tool rounds, 1–100. |
| command_timeout | integer | 600 | CLI process deadline, 1–1800 seconds; accepted gateway work can continue. |

| Additional command | Parameters | Result |
|---|---|---|
| hermes_version | none | Installed upstream version and provenance. |
| hermes_setup_check | none | Read-only CLI/version/provider-key diagnostic. |
| run | script: string = main.py | Local Python stdout (compatibility). |

Named-command results are buffered rather than streamed. `cwd` must be an existing directory satisfying the template's path constraints. Editing/tool permission allows model actions with the sandbox user's authority. Client disconnect is not a cancellation mechanism.

## Configuration

`WORKSPACE=/home/user/app`; `HERMES_HOME=/home/user/.hermes`; `HERMES_PROVIDER=openrouter`. Supply `HERMES_MODEL` or the model argument. OpenRouter requires `OPENROUTER_API_KEY`; openai-api/custom require `OPENAI_API_KEY`. Custom also requires `OPENAI_BASE_URL`. The command uses `-Q --yolo`, terminal/file toolsets and the local terminal backend. It ignores user config and rules, does not run interactive setup, and kills the owned process group on timeout. Hermes may persist session/memory state under HERMES_HOME. Its CLI auto-starts the canonical gateway when needed; that detached authority exits after upstream idle conditions are satisfied. Killing the CLI does not cancel an accepted gateway turn. Messaging adapters are not configured, while the internal canonical gateway is part of this upstream CLI execution path.

Secret declarations in template.yaml are empty; do not copy credentials into images or logs.

Hermes runs through its private Python 3.14 shebang. The image exposes only its `hermes` launcher on the platform PATH; `python3` and `agent-sandbox-server` continue to use the server environment. For local direct `python3 commands.py` development, select the environment with agent-sandbox-server installed; placing the entire Hermes venv first on PATH would select a different interpreter.

## Resources

2 vCPU, 2048 MB RAM, application port 9000, non-root `user`. Working directory: `/home/user/app`. Disk capacity and lifetime depend on the selected platform. Model tasks require outbound access to the configured model service and incur that service's charges.

## Contributing

To develop the template, read [CONTRIBUTING](../CONTRIBUTING.md) and the [design](../docs/design/hermes-agent.md).

## Issues

[Template issues](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues). [Python SDK/server issues](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues); [CLI issues](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Include sanitized commands, versions and provider; omit keys.

## License

Apache-2.0 template code. Upstream tools retain their own licenses and attribution. See [LICENSE](../LICENSE).
