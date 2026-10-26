# Factory Droid

## What it does

Run a pinned Factory Droid CLI. `droid_byok` uses an explicit compatible model, while `droid` uses a Factory account; both are headless commands.

Run Factory Droid 0.241.1 headlessly on an existing project. Named commands expose a bounded coding call, the installed version, and a setup inspection without calling a model.

## Stack

The default recipe uses the Alibaba FC generation-2 base, non-root `user`, and the published `agent-sandbox-server==0.4.0a6` package.

Original `@factory/cli@0.241.1` with its matching Linux x86_64 native package.

[Dockerfile](Dockerfile) · [template.yaml](template.yaml) · [upstream notice](UPSTREAM-NOTICE.md)

## Problem solved

Use an installed tool in an isolated sandbox, submit work through CLI, Python or HTTP, then export the files. Configure model and cloud-sandbox credentials separately.

## Quick start (CLI)

Install the CLI/Python client and configure your platform (Sandbox API key, connection address and build image registry) using the [usage guide](../docs/using-templates.md#installation), then set the separate model/application credentials below. Launching the public recipe does not require a repository checkout.

The example uses `droid_byok` with an explicit compatible Chat Completions custom model; no Factory account or browser login is needed. Its allowed tools edit/read files, so run the generated Python program separately. The separate `droid` command requires a genuine `FACTORY_API_KEY` from [Factory settings](https://app.factory.ai/settings/api-keys); model keys cannot replace it.

For the DashScope base below, create a Beijing-region key following [Model Studio API-key setup](https://www.alibabacloud.com/help/en/model-studio/get-api-key) and use a model allowed for that account. Other regions and Coding Plans use their matching keys/endpoints.

Replace every `<...>` placeholder with your own value; use an exact model ID available to your account. Set secrets in your own terminal or secret manager, never in the image, YAML or public logs. Configure these variables **before** launch; later host changes do not reconfigure the running application.

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export DROID_MODEL_API_KEY='<your-model-or-vendor-key>'
export DROID_MODEL_BASE_URL='https://dashscope.aliyuncs.com/compatible-mode/v1'
export DROID_MODEL='<model-id-from-your-provider>'
abx template launch Alibaba-Agent-Sandbox/awesome-templates//droid --sandbox-timeout 1800 --yes
export SANDBOX_ID='<sandbox-id-returned-by-launch>'
abx sandbox command list "$SANDBOX_ID"
```

`--sandbox-timeout 1800` is the sandbox lifetime in seconds; `command_timeout`/`timeout_s` limits one task, while `ABX_HTTP_TIMEOUT`/SDK `timeout` controls client waiting. These are separate limits.

Launch starts this instance's application; do not create a second sandbox or second server. For OpenSandbox, follow its [setup](../docs/using-templates.md#cli-sdk-and-http) and set `ABX_PROVIDER=opensandbox`; the Python examples below read that same choice.

```bash
ABX_HTTP_TIMEOUT=420 abx run "$SANDBOX_ID" droid_byok --json-args '{"prompt":"Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.","cwd":"/home/user/app","command_timeout":300}'
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
            print(await client.commands.run('droid_byok', prompt='Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.', cwd='/home/user/app', command_timeout=300))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

## Quick start (HTTP POST)

Use the [direct HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserving gateway headers, URL path/query and the independent application token. Send `POST /commands/droid_byok` with `Content-Type: application/json` and this direct argument object, without an `args` wrapper:

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

| Command | Parameters | Result / upstream call |
| --- | --- | --- |
| `droid_byok` | Required `prompt: str`,1–32768 UTF-8 bytes, nonempty/no NUL; `cwd: str=""`, at most4096 bytes, existing resolved workspace directory; `command_timeout: int=300`,1–600seconds, bool refused | Object: native `stdout`, `stderr`, `exit_code`, `native_version`. Fixed `droid exec --model custom:<configured-model> --output-format json --auto low --disable-builtin-skills --settings <private-settings> --only-tools Read,Edit,Create,Grep,Glob,LS`; task via anonymous stdin. Modifies the selected project; private state removed on every path. |
| `droid_byok_setup_check` | None | Model/base/key presence booleans, `mode: openai-compatible-byok`, `factory_account_required: false`; no model request or secret values. |
| `droid_version` | None | Version string from `droid --version`; no model key needed. |
| `droid_setup_check` | None | Object with `installed` (bool), `package`, `version`, `expected_version` (strings), `api_key_set`, `workspace_exists`, `auto_update_enabled` (bool). No model call; no key values returned. |
| `droid` | `prompt`: required nonempty string; `auto`: string, default `low`, one of `""`, `low`, `medium`, `high`; `cwd`: string, default `""`, existing directory within `WORKSPACE`; `command_timeout`: integer, default 300, range 1–600 seconds | Buffered stdout string from `droid exec [--auto LEVEL] -- PROMPT`. Nonzero exit or timeout raises a sanitized execution error. |

Named-command results are buffered rather than streamed. `cwd` must be an existing directory satisfying the template's path constraints. Editing/tool permission allows model actions with the sandbox user's authority. Client disconnect is not a cancellation mechanism.

## Configuration

This subprocess lifecycle requires Linux. The command closes its owned process group on success and error as well as at the deadline. It drains both output pipes while keeping the leader unreaped until group cleanup, so redirected background descendants cannot outlive a completed command.

| Name | Default | Purpose |
| --- | --- | --- |
| `DROID_MODEL_API_KEY` | Empty; required for BYOK | At most8192 characters, no CR/LF/NUL; private native environment only. |
| `DROID_MODEL_BASE_URL` | Empty; required for BYOK | Explicit HTTPS compatible base, at most2048 characters, no userinfo/query/fragment; literal local HTTP only for fixtures. |
| `DROID_MODEL` | Empty; required for BYOK | Explicit1–200-character model identifier. |
| `FACTORY_API_KEY` | Empty | Factory account API key, injected at creation. Required only for `droid`. |
| `ABX_SERVER_TOKEN` | empty | Export an independent application token before the template launch; separate from model and gateway credentials |
| `WORKSPACE` | `/home/user/app` | Existing project root; an invalid explicit root fails. |
| `FACTORY_DROID_AUTO_UPDATE_ENABLED` | `false` | Forced off in subprocesses to preserve the pin. |

Factory credentials are obtained from [Factory API key settings](https://app.factory.ai/settings/api-keys). A DashScope or OpenAI key is not a replacement for `FACTORY_API_KEY`. `droid_byok` instead uses a private native `customModels` entry, provider `generic-chat-completion-api`, explicit model/base and `apiKey: "${ABX_DROID_MODEL_KEY}"`. The real key is not written into settings or argv. Native selection uses the configured custom model; no Factory key, interactive login or alternate binary is injected. Key/base values are redacted from native output; private state is deleted. [Official BYOK docs](https://docs.factory.com/model-independence/byok). Upstream behavior is documented in [Droid Exec](https://docs.factory.com/droid-exec/overview); the exact pinned CLI help is the authority for flags. Redaction covers raw and JSON-escaped configured secret values in stdout and error messages. Agent-written project files still require normal secret hygiene. The cwd constraint selects the project and is not an operating-system security boundary.

## Resources

2 vCPU, 2048 MB RAM, application port 9000, non-root `user`. Working directory: `/home/user/app`. Disk capacity and lifetime depend on the selected platform. Model tasks require outbound access to the configured model service and incur that service's charges.

## Contributing

To develop the template, read [CONTRIBUTING](../CONTRIBUTING.md) and the [design](../docs/design/droid.md).

## Issues

Continue [Droid issue #19](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/19). Report template defects in [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues), client/server defects in [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), or CLI defects in [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Include versions, provider, generation and sanitized reproduction; never include keys or raw private logs.

## License

Template source: [Apache-2.0](../LICENSE). Factory Droid is distributed separately under its upstream terms; installing the CLI does not relicense it.
