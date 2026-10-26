# Cursor Agent

[中文](README.zh-CN.md).

## What it does

Run the original Cursor Agent CLI in an owned disposable sandbox through typed named commands. Cursor owns inference and tool execution. A genuine CURSOR_API_KEY is required for agent tasks; no compatible-model or operator-key fallback exists. Automatic native tools require explicit `allow_unsafe_tools=True`.

## Stack

The default recipe uses the Alibaba FC generation-2 base, non-root `user`, and the published `agent-sandbox-server==0.4.0a6` package.

Original Cursor Agent CLI `2026.10.19-6bbf2c4` for Linux x86_64, including its bundled Node runtime.

[Dockerfile](Dockerfile) · [template.yaml](template.yaml) · [upstream notice](UPSTREAM-NOTICE.md)

## Problem solved

Use an installed tool in an isolated sandbox, submit work through CLI, Python or HTTP, then export the files. Configure model and cloud-sandbox credentials separately.

## Quick start (CLI)

Install the CLI/Python client and configure your platform (Sandbox API key, connection address and build image registry) using the [usage guide](../docs/using-templates.md#installation), then set the separate model/application credentials below. Launching the public recipe does not require a repository checkout.

Create a personal User API Key in Cursor Dashboard → API Keys/Integrations, then follow [Cursor CLI authentication](https://cursor.com/help/integrations/cli). This headless wrapper uses `CURSOR_API_KEY`, not browser login or an OpenAI key. The optional command `model` selects a model available to that Cursor account; arbitrary model API endpoints are not exposed.

Replace every `<...>` placeholder with your own value; use an exact model ID available to your account. Set secrets in your own terminal or secret manager, never in the image, YAML or public logs. Configure these variables **before** launch; later host changes do not reconfigure the running application.

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export CURSOR_API_KEY='<your-model-or-vendor-key>'
abx template launch Alibaba-Agent-Sandbox/awesome-templates//cursor-agent --sandbox-timeout 1800 --yes
export SANDBOX_ID='<sandbox-id-returned-by-launch>'
abx sandbox command list "$SANDBOX_ID"
```

`--sandbox-timeout 1800` is the sandbox lifetime in seconds; `command_timeout`/`timeout_s` limits one task, while `ABX_HTTP_TIMEOUT`/SDK `timeout` controls client waiting. These are separate limits.

Launch starts this instance's application; do not create a second sandbox or second server. For OpenSandbox, follow its [setup](../docs/using-templates.md#cli-sdk-and-http) and set `ABX_PROVIDER=opensandbox`; the Python examples below read that same choice.

```bash
ABX_HTTP_TIMEOUT=420 abx run "$SANDBOX_ID" agent --json-args '{"prompt":"Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.","allow_unsafe_tools":true,"cwd":"/home/user/app","command_timeout":300}'
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
            print(await client.commands.run('agent', prompt='Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.', allow_unsafe_tools=True, cwd='/home/user/app', command_timeout=300))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

## Quick start (HTTP POST)

Use the [direct HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserving gateway headers, URL path/query and the independent application token. Send `POST /commands/agent` with `Content-Type: application/json` and this direct argument object, without an `args` wrapper:

```json
{
  "prompt": "Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.",
  "allow_unsafe_tools": true,
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

| Command | Parameters | Result / side effects |
| --- | --- | --- |
| agent_version | none | Fixed native version string; validates all original files before running --version |
| agent_native_check | none | original_native/headless_print/json_output/explicit_force/contained_workspace booleans; original --help; no model |
| agent_setup_check | none | mode/installed/pinned_version/api_key_set/requires_unsafe_optin/vendor_authentication_verified/compatible_model_fallback; presence only, no values/network |
| agent | prompt required string; cwd string default empty; command_timeout integer300; allow_unsafe_tools booleanFalse; model string default empty | Buffered original final; may read/write/run tools only after explicit opt-in |

Named-command results are buffered rather than streamed. `cwd` must be an existing directory satisfying the template's path constraints. Editing/tool permission allows model actions with the sandbox user's authority. Client disconnect is not a cancellation mechanism. Model calls are serialized; overlapping requests fail busy. Cleanup can extend response time; the examples leave an HTTP waiting margin.

## Configuration

| Variable | Default / requirement | Meaning |
| --- | --- | --- |
| CURSOR_API_KEY | empty; required for agent | Genuine vendor credential captured when the server imports commands |
| WORKSPACE | /home/user/app | Contained project root, captured at import |
| ABX_SERVER_TOKEN | required; empty declaration | Export an independent application token before the template launch; separate from model and gateway credentials |

Original programs receive a minimal environment with only their explicit vendor key and private HOME/config/data/cache/TMP paths. Updates and project configuration loading are disabled by pinned original flags; OS keychain/persistent native sessions are not used. Per-call native state is removed after success/error/timeout. The server process and native tools share an OS user; these paths are not another tenant boundary. Use a fresh caller-owned disposable sandbox for automatic tools.

At most one agent operation per server process; concurrent calls fail busy. Stdout/stderr are each bounded256KiB, command deadline1..600seconds plus up to90seconds cleanup; client timeout should cover command_timeout+120seconds. Known key/command-token/private-home values are redacted. No private transcript or provider ID belongs in public evidence.

## Resources

2 vCPU, 4096 MB RAM, application port 9000, non-root `user`. Working directory: `/home/user/app`. Disk capacity and lifetime depend on the selected platform. Model tasks require outbound access to the configured model service and incur that service's charges. This pinned installation targets Linux x86_64.

## Contributing

To develop the template, read [CONTRIBUTING](../CONTRIBUTING.md) and the [design](../docs/design/cursor-agent.md).

## Issues

[Issue63](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/63), [templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues), [SDK](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), [CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Upstream behavior belongs to Cursor. Do not attach credentials/private transcripts.

## License

Authored template Apache-2.0. Original Anysphere software and bundled third-party licenses retain their own terms/notices; see [notice](UPSTREAM-NOTICE.md). No vendor endorsement or redistribution of its binary/source in this Git repository is asserted.
