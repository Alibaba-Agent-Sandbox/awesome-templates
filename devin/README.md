# devin

[中文](README.zh-CN.md).

## What it does

Run the original Cognition Devin CLI3000.11.92 through typed bounded named commands in an owned disposable sandbox. The native CLI owns inference and tools; no replacement planner or compatible-model fallback is supplied. Automatic tools require `allow_unsafe_tools=True`.

## Stack

The default recipe uses the Alibaba FC generation-2 base, non-root `user`, and the published `agent-sandbox-server==0.4.0a6` package.

Original Devin CLI `3000.11.92` for Linux x86_64, with its bundled binaries and notices.

[Dockerfile](Dockerfile) · [template.yaml](template.yaml) · [upstream notice](UPSTREAM-NOTICE.md)

## Problem solved

Use an installed tool in an isolated sandbox, submit work through CLI, Python or HTTP, then export the files. Configure model and cloud-sandbox credentials separately.

## Quick start (CLI)

Install the CLI/Python client and configure your platform (Sandbox API key, connection address and build image registry) using the [usage guide](../docs/using-templates.md#installation), then set the separate model/application credentials below. Launching the public recipe does not require a repository checkout.

Authenticated coding requires a genuine original Devin `credentials.toml`, created by signing in with the original CLI on a trusted machine. See [Devin CLI](https://docs.devin.ai/work-with-devin/devin-cli) for account setup. There is no invented `DEVIN_API_KEY` or generic model endpoint. `DEVIN_CREDENTIALS_FILE` must name a private file INSIDE the sandbox, outside `WORKSPACE`; a local host pathname is not uploaded automatically. The file is read when a task runs, so upload it after launch using the steps below. Without an authorized account file, setup/version works but coding fails with the native login refusal.

First install the original CLI on your trusted machine following the linked official instructions, then run `devin auth login`. Your Devin Enterprise role must permit CLI access. The [official authentication guide](https://docs.devin.ai/cli/enterprise/devin-auth) places the file at `$XDG_DATA_HOME/devin/credentials.toml`, or `~/.local/share/devin/credentials.toml` when XDG_DATA_HOME is unset, on macOS/Linux; Windows uses `%APPDATA%\devin\credentials.toml`.

Replace every `<...>` placeholder with your own value; use an exact model ID available to your account. Set secrets in your own terminal or secret manager, never in the image, YAML or public logs. Configure these variables **before** launch; later host changes do not reconfigure the running application.

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export DEVIN_CREDENTIALS_FILE='/home/user/devin-private/credentials.toml'
abx template launch Alibaba-Agent-Sandbox/awesome-templates//devin --sandbox-timeout 1800 --yes
export SANDBOX_ID='<sandbox-id-returned-by-launch>'
abx sandbox command list "$SANDBOX_ID"
```

`--sandbox-timeout 1800` is the sandbox lifetime in seconds; `command_timeout`/`timeout_s` limits one task, while `ABX_HTTP_TIMEOUT`/SDK `timeout` controls client waiting. These are separate limits.

Launch starts this instance's application; do not create a second sandbox or second server. For OpenSandbox, follow its [setup](../docs/using-templates.md#cli-sdk-and-http) and set `ABX_PROVIDER=opensandbox`; the Python examples below read that same choice.

After native login on your trusted machine, replace the local pathname below with your own generated credentials.toml; do not print its content:

```bash
abx exec "$SANDBOX_ID" -- mkdir -p /home/user/devin-private
abx exec "$SANDBOX_ID" -- chmod 700 /home/user/devin-private
abx upload "$SANDBOX_ID" "<local-credentials.toml>" /home/user/devin-private/credentials.toml
abx exec "$SANDBOX_ID" -- chmod 600 /home/user/devin-private/credentials.toml
```

```bash
ABX_HTTP_TIMEOUT=420 abx run "$SANDBOX_ID" devin --json-args '{"prompt":"Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.","allow_unsafe_tools":true,"cwd":"/home/user/app","command_timeout":300}'
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
            print(await client.commands.run('devin', prompt='Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.', allow_unsafe_tools=True, cwd='/home/user/app', command_timeout=300))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

## Quick start (HTTP POST)

Use the [direct HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserving gateway headers, URL path/query and the independent application token. Send `POST /commands/devin` with `Content-Type: application/json` and this direct argument object, without an `args` wrapper:

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

| Command | Arguments | Result/side effects |
| --- | --- | --- |
| devin_version | none | Original file identity + actual `--version` string |
| devin_native_check | none | Original `--help`; original_native/headless_print/private_config/explicit_permission/workspace_trust_control booleans |
| devin_setup_check | none | mode/installed/pinned_version/credentials_file_set/requires_unsafe_optin/vendor_authentication_verified/compatible_model_fallback; presence only |
| devin | prompt:string required; cwd:string empty; command_timeout:int300; allow_unsafe_tools:boolFalse; model:string empty | Buffered original final stdout; explicit opt-in permits native file/tool actions |

Named-command results are buffered rather than streamed. `cwd` must be an existing directory satisfying the template's path constraints. Editing/tool permission allows model actions with the sandbox user's authority. Client disconnect is not a cancellation mechanism. Model calls are serialized; overlapping requests fail busy. Cleanup can extend response time; the examples leave an HTTP waiting margin.

## Configuration

| Setting | Default/requirement | Meaning |
| --- | --- | --- |
| DEVIN_CREDENTIALS_FILE | empty; optional for diagnostics/error-path, required for account tasks | Authored wrapper input path captured at module import; absolute, outside WORKSPACE, regular nonsymlink owned by root/current UID, no group/other permissions,1..65536bytes valid UTF8TOML |
| WORKSPACE | /home/user/app | Captured existing project root |
| ABX_SERVER_TOKEN | required; empty declaration | Export an independent application token before the template launch; separate from model and gateway credentials |

A missing original account file reaches original print and preserves its explicit login refusal; no interactive login, made-up DEVIN_API_KEY, root model key or fallback planner is used. The subprocess receives minimal private state environment without operator/model/cloud credentials or the source credential path. Known credential TOML string values, server Bearer/private HOME/source path are redacted in returned stdout. Native errors omit raw output. One operation per server process; overlap returns busy.

Each stdout/stderr stream is bounded256KiB; command1..600seconds plus up to90seconds owned descendant cleanup. Set client timeout at least command_timeout+120seconds. Same OS user/tool permissions are not a multi-tenant filesystem security boundary. Use owned disposable sandboxes with explicitly trusted task content; the native program can execute tools under that account.

## Resources

2 vCPU, 4096 MB RAM, application port 9000, non-root `user`. Working directory: `/home/user/app`. Disk capacity and lifetime depend on the selected platform. Model tasks require outbound access to the configured model service and incur that service's charges. This pinned installation targets Linux x86_64.

## Contributing

To develop the template, read [CONTRIBUTING](../CONTRIBUTING.md) and the [design](../docs/design/devin.md).

## Issues

[Issue72](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/72), [templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues), [SDK](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), [CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Vendor login/model behavior belongs to Cognition. Never attach credentials/private transcripts.

## License

Authored template Apache-2.0. Original Cognition software/docs/manpages retain separate terms; see [notice](UPSTREAM-NOTICE.md). No original binary/source is committed or relicensed; no vendor endorsement/independent redistribution grant is asserted.
