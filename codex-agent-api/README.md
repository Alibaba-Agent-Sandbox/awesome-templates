# codex-agent-api

## What it does

A project-defined HTTP session adapter that calls the official Codex CLI for every turn. The image pins `@openai/codex@0.162.1`, matching the [`codex`](../codex) template. It offers named commands and `/v1/agents/*` routes through `agent-sandbox-server` on port 9000. This is a limited session API; compatibility with every OpenAI Agents API feature or SDK method has not been established. Use the HTTP contract below rather than assuming a particular `client.beta.agents` interface exists.

Each turn uses `codex exec --json`. New sessions start a fresh Codex thread; later turns resume that exact thread id. A background monitor drains stdout and stderr concurrently, enforces a 300-second deadline even without a subscriber, and terminates the CLI process group on timeout, session deletion, or shutdown. Multiple subscribers read a bounded replay buffer rather than competing for stdout.

## Stack

The default recipe uses the Alibaba FC generation-2 base, non-root `user`, and the published `agent-sandbox-server==0.4.0a6` package.

Official Codex CLI `0.162.1`, Node.js 20, and the template session API on port 9000.

[Dockerfile](Dockerfile) · [template.yaml](template.yaml)

## Problem solved

Use an installed tool in an isolated sandbox, submit work through CLI, Python or HTTP, then export the files. Configure model and cloud-sandbox credentials separately.

## Quick start (CLI)

Install the CLI/Python client and configure your platform (Sandbox API key, connection address and build image registry) using the [usage guide](../docs/using-templates.md#installation), then set the separate model/application credentials below. Launching the public recipe does not require a repository checkout.

The configured model service must implement HTTP Responses, not only Chat Completions. `ABX_LLM_API_KEY` supplies the custom provider key; do not leave a conflicting `OPENAI_BASE_URL` in the launch environment because that URL takes precedence here. API-key mode does not require interactive login. `CODEX_SANDBOX` defaults to `workspace-write`; use the existing `bypass` option only when your platform cannot run nested Codex sandboxing and you accept the owned outer sandbox as the boundary.

Before running a coding task, check whether your platform supports Codex's nested Linux sandbox. On a platform that refuses it, the public recipe's fixed `CODEX_SANDBOX=workspace-write` cannot be changed by exporting a host value. If you deliberately choose the outer sandbox as the isolation boundary, clone the repository, change `env.CODEX_SANDBOX` to `bypass` in `codex-agent-api/template.yaml`, and use `abx template launch ./codex-agent-api --sandbox-timeout 1800 --yes` instead of the public recipe command below.

Replace every `<...>` placeholder with your own value; use an exact model ID available to your account. Set secrets in your own terminal or secret manager, never in the image, YAML or public logs. Configure these variables **before** launch; later host changes do not reconfigure the running application.

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ABX_LLM_API_KEY='<your-model-or-vendor-key>'
export ABX_LLM_BASE_URL='https://api.openai.com/v1'
export CODEX_MODEL='<model-id-from-your-Responses-provider>'
abx template launch Alibaba-Agent-Sandbox/awesome-templates//codex-agent-api --sandbox-timeout 1800 --yes
export SANDBOX_ID='<sandbox-id-returned-by-launch>'
abx sandbox command list "$SANDBOX_ID"
```

`--sandbox-timeout 1800` is the sandbox lifetime in seconds; `command_timeout`/`timeout_s` limits one task, while `ABX_HTTP_TIMEOUT`/SDK `timeout` controls client waiting. These are separate limits.

Launch starts this instance's application; do not create a second sandbox or second server. For OpenSandbox, follow its [setup](../docs/using-templates.md#cli-sdk-and-http) and set `ABX_PROVIDER=opensandbox`; the Python examples below read that same choice.

```bash
ABX_HTTP_TIMEOUT=420 abx run "$SANDBOX_ID" codex --json-args '{"prompt":"Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.","timeout_s":300}'
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
            print(await client.commands.run('codex', prompt='Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.', timeout_s=300))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

## Quick start (HTTP POST)

Use the [direct HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserving gateway headers, URL path/query and the independent application token. Send `POST /commands/codex` with `Content-Type: application/json` and this direct argument object, without an `args` wrapper:

```json
{
  "prompt": "Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.",
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

| Command | Parameters (type; required/default) | Result | Upstream argv |
|---|---|---|---|
| `codex_version` | None | Version string | `codex --version` |
| `agent_status` | None | JSON-encoded list of session id/status/model | None |
| `codex` | `prompt` str required; `model` str `""`; `timeout_s` int `300` (1–3600) | `{thread_id, events, status, events_truncated}`; failures raise RuntimeError | `codex exec --json --color never --skip-git-repo-check [provider/sandbox/model config] -- <prompt>` |

| Method and path | Parameters / behavior |
|---|---|
| `POST /v1/agents` | `model` str `""`, `instructions` str `""`, `tools` list `[]`, `name` str `""`, `metadata` object `{}`; returns saved config with `agent_*` id |
| `GET /v1/agents` | `{object:"list",data:[...]}` |
| `GET /v1/agents/{id}` | Saved configuration |
| `POST /v1/agents/{id}` | Update the same configuration fields |
| `DELETE /v1/agents/{id}` | `{id,object,deleted:true}` |
| `POST /v1/agents/sessions` | `agent` inline `{model,instructions,tools}` or saved id (default `{}`); `input` str or `[{type:"input_text",text:...}]` optional; `stream` bool false; `background` bool false |
| `GET /v1/agents/sessions` | Session list |
| `GET /v1/agents/sessions/{id}` | Status, configuration, last five retained output items, cumulative input/output token usage |
| `POST /v1/agents/sessions/{id}` | Update `model` / `instructions` |
| `DELETE /v1/agents/sessions/{id}` | Delete and terminate the active CLI/tool process group |
| `POST /v1/agents/sessions/{id}/events` | Required `input` text (same shapes), or `{type:"agent.session.input.message",content:[{type:"input_text",text:...}]}`; `stream` bool defaults true; `background` bool false (disables default streaming) |
| `GET /v1/agents/sessions/{id}/events` | Replay retained events and subscribe while active; idle session returns JSON status |
| `GET /v1/agents/sessions/{id}/items` | Retained Codex item events |
| `GET /v1/agents/sessions/{id}/artifacts/{artifact_id}` | UTF-8 text artifact up to 1 MB; id is URL-safe base64 of workspace-relative path |
| `DELETE /v1/agents/sessions/{id}/artifacts/{artifact_id}` | Remove artifact within workspace |

Named-command results are buffered rather than streamed. `cwd` must be an existing directory satisfying the template's path constraints. Editing/tool permission allows model actions with the sandbox user's authority. Client disconnect is not a cancellation mechanism.

## Configuration

| Environment variable | Default / meaning |
|---|---|
| `OPENAI_API_KEY`, `CODEX_API_KEY`, `ABX_LLM_API_KEY` | Empty; runtime secrets. ABX key fills OPENAI key only when unset; direct OpenAI uses CODEX key, with OPENAI fallback |
| `OPENAI_BASE_URL`, `ABX_LLM_BASE_URL` | Empty; OPENAI URL wins. Custom provider uses HTTP Responses API (`wire_api="responses"`, websockets disabled) |
| `CODEX_MODEL`, `ABX_LLM_MODEL` | Empty; CODEX wins, otherwise upstream configured model |
| `CODEX_SANDBOX` | `workspace-write`; accepts `read-only`, `workspace-write`, `danger-full-access`, `bypass` |
| `CODEX_HOME` | Image sets `/home/user/.codex`; keep outside workspace/artifacts |
| `WORKSPACE` | `/home/user/workspace` |
| `AGENT_MAX_SESSIONS` | `20` |
| `AGENT_SESSION_TTL` | `1800` seconds; GC checks every 60 seconds |
| `ABX_SERVER_TOKEN` | Export an independent application token before the template launch; separate from model and gateway credentials |

The service retains at most 200 saved agent configurations; each session allows 100 turns. Replay and retained item buffers each hold at most 1000 events / 2 MB; a single JSONL line exceeding 256000 bytes fails the turn. stderr is drained continuously and only a bounded, redacted tail can be included in errors. Environment secret values, request-supplied MCP header values and bearer tokens are redacted from returned events/configurations/errors/text artifacts. Artifacts reject `.env`, `.aws`, `.codex`, `.ssh` paths and symlinks outside the workspace. This filtering supplements sandbox isolation; the standard shell/files APIs still require trusted access and server policy.

## Resources

2 vCPU, 4096 MB RAM, application port 9000, non-root `user`. Working directory: `/home/user/workspace`. Disk capacity and lifetime depend on the selected platform. Model tasks require outbound access to the configured model service and incur that service's charges.

## Contributing

To develop the template, read [CONTRIBUTING](../CONTRIBUTING.md) and the [design](../docs/design/codex-agent-api.md).

## Issues

[Template issue #23](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/23). SDK/server defects belong in [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues); CLI/deploy defects belong in [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues), with `[templates]` title prefix.

## License

Apache-2.0. Codex and dependencies retain their respective upstream licenses.
