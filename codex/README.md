# codex

Non-interactive [OpenAI Codex CLI](https://github.com/openai/codex) in an Agent Sandbox. The image pins `@openai/codex@0.162.1`.

## What it does

Named commands on `agent-sandbox-server` (port 9000) call `codex exec`. `codex_exec` returns JSONL events (`thread.started`, `turn.*`, `item.*`), the last agent message, and the `thread_id` used to resume. `codex_version` prints the CLI version. `codex_setup_check` probes Codex's Linux sandbox and reports `--dangerously-bypass-approvals-and-sandbox` when bubblewrap, seccomp, or the legacy landlock path cannot start. `codex_config_write` writes `$CODEX_HOME/config.toml` for an OpenAI-compatible `base_url` (`wire_api = "responses"` only). `codex_agents_write` writes `AGENTS.md`, which Codex reads from the working directory.

Codex 0.162.1 does not accept the old `codex -p ... --output-format json` argv, and it rejects `--full-auto`.

The standalone `apply_patch` binary is a different template (issue #60). The Agents API HTTP service is `codex-agent-api` (issue #23). See [docs/design/codex.md](../docs/design/codex.md).

## Stack

The default recipe uses the Alibaba FC generation-2 base, non-root `user`, and the published `agent-sandbox-server==0.4.0a6` package.

Official `@openai/codex@0.162.1`, Node.js 20, Git, ripgrep and jq. The CLI package includes its own Linux sandbox helper.

[Dockerfile](Dockerfile) · [template.yaml](template.yaml)

## Problem solved

Use an installed tool in an isolated sandbox, submit work through CLI, Python or HTTP, then export the files. Configure model and cloud-sandbox credentials separately.

## Quick start (CLI)

Install the CLI/Python client and configure your platform (Sandbox API key, connection address and build image registry) using the [usage guide](../docs/using-templates.md#installation), then set the separate model/application credentials below. Launching the public recipe does not require a repository checkout.

The custom provider requires the HTTP Responses API (`/responses`), not only Chat Completions (`/chat/completions`). Use the endpoint and model offered by your Responses provider; a DashScope Chat endpoint is not automatically compatible. The wrapper writes the provider configuration under `CODEX_HOME`; `ABX_LLM_API_KEY` is its explicit key. No interactive ChatGPT login is needed for this API-key path. Default `sandbox="auto"` may select bypass when nested Linux sandboxing is unavailable: use an owned disposable outer sandbox.

Replace every `<...>` placeholder with your own value; use an exact model ID available to your account. Set secrets in your own terminal or secret manager, never in the image, YAML or public logs. Configure these variables **before** launch; later host changes do not reconfigure the running application.

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ABX_LLM_API_KEY='<your-model-or-vendor-key>'
export ABX_LLM_BASE_URL='https://api.openai.com/v1'
export CODEX_MODEL='<model-id-from-your-Responses-provider>'
abx template launch Alibaba-Agent-Sandbox/awesome-templates//codex --sandbox-timeout 1800 --yes
export SANDBOX_ID='<sandbox-id-returned-by-launch>'
abx sandbox command list "$SANDBOX_ID"
```

`--sandbox-timeout 1800` is the sandbox lifetime in seconds; `command_timeout`/`timeout_s` limits one task, while `ABX_HTTP_TIMEOUT`/SDK `timeout` controls client waiting. These are separate limits.

Launch starts this instance's application; do not create a second sandbox or second server. For OpenSandbox, follow its [setup](../docs/using-templates.md#cli-sdk-and-http) and set `ABX_PROVIDER=opensandbox`; the Python examples below read that same choice.

```bash
ABX_HTTP_TIMEOUT=420 abx run "$SANDBOX_ID" codex_exec --json-args '{"prompt":"Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.","sandbox":"auto","cwd":"/home/user/workspace","timeout_s":300}'
```

The task creates `generated_hello.py` and `GENERATED_REPORT.md` in `/home/user/workspace`. The example explicitly enables the required editing/tools; use an owned disposable sandbox. The SDK and HTTP examples are alternative ways to submit the same task; choose one.

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
            print(await client.commands.run('codex_exec', prompt='Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.', sandbox='auto', cwd='/home/user/workspace', timeout_s=300))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

## Quick start (HTTP POST)

Use the [direct HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserving gateway headers, URL path/query and the independent application token. Send `POST /commands/codex_exec` with `Content-Type: application/json` and this direct argument object, without an `args` wrapper:

```json
{
  "prompt": "Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.",
  "sandbox": "auto",
  "cwd": "/home/user/workspace",
  "timeout_s": 300
}
```

The response is `{"result": ...}`; see the command reference for its actual content type. Model text varies. Set the HTTP wait to at least 420 seconds; the command execution deadline is separate, and disconnecting does not guarantee remote cancellation. Authentication failures return 401, invalid argument types 400, and execution errors an error response. If a result includes `exit_code`, also check that it is zero.

### Export files and cleanup

```bash
abx exec "$SANDBOX_ID" -- python3 /home/user/workspace/generated_hello.py
abx download "$SANDBOX_ID" /home/user/workspace/generated_hello.py ./generated_hello.py
abx download "$SANDBOX_ID" /home/user/workspace/GENERATED_REPORT.md ./GENERATED_REPORT.md
abx kill "$SANDBOX_ID"
```

Expected program output: `Hello from the sandbox`. Inspect actual files before using them; a successful-looking model response does not guarantee files exist. Files do not automatically update the template or your machine; export them before deleting the sandbox.

`close()`/`aclose()` only close client connections; they do not delete the sandbox. Prepared templates/images in the launch journal can remain for reuse; remove only your own exact resources when no longer needed.

## Command reference

| Command | Parameters | Returns |
|---|---|---|
| `codex_version` | none | string `X.Y.Z` |
| `codex_setup_check` | none | object, probe and bypass flag |
| `codex_exec` | see the table below | object, events and last message |
| `codex_config_write` | `base_url`, `provider`, `env_key`, `model`, `wire_api`, `codex_home` | object, path and toml |
| `codex_agents_write` | `content` (required), `cwd` | object, `path` and `bytes` |

| Name | Type | Required | Default | Meaning |
|---|---|---|---|---|
| `prompt` | string | yes | | Instruction. Passed after `--`, not through a shell. |
| `model` | string | no | empty | `--model`. Empty uses config or the CLI default. |
| `cwd` | string | no | `WORKSPACE` | `-C` working root. |
| `sandbox` | string | no | `auto` | `auto`, `bypass`, `read-only`, `workspace-write`, `danger-full-access`. |
| `approval` | string | no | `never` | `untrusted`, `on-request`, `never`. Ignored when the bypass flag is used. |
| `json_events` | boolean | no | true | `--json` JSONL on stdout. |
| `resume` | string | no | empty | Session id, or `last`. |
| `resume_all` | boolean | no | false | `--all` with `resume=last`. |
| `skip_git_repo_check` | boolean | no | true | `--skip-git-repo-check`. |
| `ephemeral` | boolean | no | false | Do not persist the session. |
| `output_schema` | string | no | empty | Path of a JSON Schema file. |
| `agents_md` | string | no | empty | Written to `cwd/AGENTS.md` before exec. |
| `timeout_s` | integer | no | 300 | Process timeout, 1–3600 seconds. |

Named-command results are buffered rather than streamed. `cwd` must be an existing directory satisfying the template's path constraints. Editing/tool permission allows model actions with the sandbox user's authority. Client disconnect is not a cancellation mechanism.

## Configuration

| Name | Required | Default | Purpose |
|---|---|---|---|
| `OPENAI_API_KEY` | no | empty | Key for the built-in OpenAI provider, or the `env_key` of a compatible provider. |
| `CODEX_API_KEY` | no | empty | Codex's own API-key variable. Copied from `OPENAI_API_KEY` only when no custom `base_url` is configured. |
| `ABX_LLM_API_KEY` | no | empty | Preferred key variable when writing a config for `ABX_LLM_BASE_URL`. |
| `OPENAI_BASE_URL` | no | empty | OpenAI-compatible base URL, for example a DashScope `/compatible-mode/v1` host. |
| `ABX_LLM_BASE_URL` | no | empty | Same role as `OPENAI_BASE_URL`. Wins when both are set. |
| `CODEX_MODEL` | no | empty | `model` written into `config.toml` and used when `codex_exec` omits `model`. |
| `CODEX_HOME` | no | `/home/user/.codex` | Directory of `config.toml` and sessions. |
| `WORKSPACE` | no | `/home/user/workspace` | Default `cwd`. A starter `AGENTS.md` is in the image. |
| `ABX_SERVER_TOKEN` | yes | empty | Export an independent application token before the template launch; separate from model and gateway credentials |

Before `template launch`, securely export the secret variables declared empty in the manifest so the application reads them at startup. Keep values out of images, YAML and logs.

`codex_exec` creates `config.toml` when a base URL is set and the file is missing. `codex_config_write` overwrites the file. Codex 0.162.1 will not send Chat Completions; `wire_api = "chat"` is a hard error.

## Resources

2 vCPU, 2048 MB RAM, application port 9000, non-root `user`. Working directory: `/home/user/workspace`. Disk capacity and lifetime depend on the selected platform. Model tasks require outbound access to the configured model service and incur that service's charges.

## Contributing

To develop the template, read [CONTRIBUTING](../CONTRIBUTING.md) and the [design](../docs/design/codex.md).

## Issues

| Topic | Repository |
|---|---|
| This template, the spec, the checker | [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues) |
| Python SDK or `agent-sandbox-server` | [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), title prefix `[templates]` |
| `abx` CLI | [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues), title prefix `[templates]` |

## License

Apache-2.0, the same license as this repository. See [LICENSE](../LICENSE).
