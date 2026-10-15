# codex

Non-interactive [OpenAI Codex CLI](https://github.com/openai/codex) in an Agent Sandbox. The image pins `@openai/codex@0.162.1`.

## What it does

Named commands on `agent-sandbox-server` (port 9000) call `codex exec`. `codex_exec` returns JSONL events (`thread.started`, `turn.*`, `item.*`), the last agent message, and the `thread_id` used to resume. `codex_version` prints the CLI version. `codex_setup_check` probes Codex's Linux sandbox and reports `--dangerously-bypass-approvals-and-sandbox` when bubblewrap, seccomp, or the legacy landlock path cannot start. `codex_config_write` writes `$CODEX_HOME/config.toml` for an OpenAI-compatible `base_url` (`wire_api = "responses"` only). `codex_agents_write` writes `AGENTS.md`, which Codex reads from the working directory.

`codex` is a compatibility alias of `codex_exec` (`prompt` and `model` only). Codex 0.162.1 does not accept the old `codex -p ... --output-format json` argv, and it rejects `--full-auto`.

The standalone `apply_patch` binary is a different template (issue #60). The Agents API HTTP service is `codex-agent-api` (issue #23). See [docs/design/codex.md](../docs/design/codex.md).

## Stack

- Base image `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`. `abx template deploy` replaces `<region>` with `cn-hangzhou` (or `ALIBABA_CLOUD_REGION_ID`) and `<tag>` with `v0.0.49` (or `ABX_BASE_IMAGE_TAG`).
- Node.js 20 and Python 3.13 from that image.
- `@openai/codex@0.162.1` (`codex-cli 0.162.1`).
- `agent-sandbox-server==0.3.0` from python-sdk commit `61c43e0be65a1f57aa09186d578e7b399e48429b` when the build context has no wheel.
- `git`, `ripgrep`, `jq`. System `bubblewrap` is not installed, so Codex uses the `bwrap` shipped inside the npm package.
- Work directory `/home/user/app`. Workspace `/home/user/workspace`. Runtime user `user`. No image `CMD` or `ENTRYPOINT`.

## Problem solved

Gives a sandbox a pinned, non-interactive Codex CLI: JSON events, an explicit working directory, resume, a generated provider config for DashScope-style OpenAI-compatible endpoints, and a sandbox probe that does not assume landlock or user namespaces exist. Callers use `abx run` or `Sandbox.run` instead of embedding CLI flags in a shell string.

## Quick start (CLI)

From a checkout of this repository, with Express credentials in the environment:

```bash
abx template deploy ./codex -y --generation 2 \
  --start-cmd 'agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py' \
  --ready-cmd 'agent-sandbox-server healthcheck --port 9000'
abx create --template <template-id> -y \
  --env OPENAI_API_KEY=<key> \
  --env OPENAI_BASE_URL=<https://host/compatible-mode/v1> \
  --env CODEX_MODEL=qwen-plus
abx run <sandbox-id> codex_version
abx run <sandbox-id> codex_setup_check
abx run <sandbox-id> codex_exec --json-args '{"prompt":"Summarize the workspace.","model":"qwen-plus"}'
```

`template.yaml` already stores `generation`, `start_cmd`, and `ready_cmd`.

Remove the sandbox and the template when you are done:

```bash
abx kill <sandbox-id> -y
abx template delete <template-id> -y
```

`python3 scripts/express_e2e.py codex` deploys a unique alias, runs the smoke commands, writes evidence only after a pass, and deletes that sandbox and that template.

## Quick start (Python SDK)

```python
import asyncio
from agent_sandbox import Sandbox

async def main() -> None:
    sb = await Sandbox.create(
        template="<template-id>",
        timeout=300,
        envs={
            "OPENAI_API_KEY": "<key>",
            "OPENAI_BASE_URL": "https://host/compatible-mode/v1",
            "CODEX_MODEL": "qwen-plus",
        },
    )
    try:
        print(await sb.run("codex_version"))
        print(await sb.run(
            "codex_exec",
            prompt="Reply with exactly: ABX_E2E_OK",
            model="qwen-plus",
            sandbox="auto",
        ))
    finally:
        await sb.kill()

asyncio.run(main())
```

`await sb.run("codex_exec", prompt="...")` returns the result object (`last_message`, `events`, `thread_id`). `sb.commands.run` is a shell command, not this named command. `Sandbox.create_sync` raises `TypeError` on python-sdk 0.3.0 ([python-sdk#22](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues/22)); use `await Sandbox.create`.

Resume with the `thread_id` from the first result:

```python
await sb.run("codex_exec", prompt="Continue.", resume="<thread_id>")
```

## Command reference

| Command | Parameters | Returns |
|---|---|---|
| `codex_version` | none | string `X.Y.Z` |
| `codex_setup_check` | none | object, probe and bypass flag |
| `codex_exec` | see the table below | object, events and last message |
| `codex_config_write` | `base_url`, `provider`, `env_key`, `model`, `wire_api`, `codex_home` | object, path and toml |
| `codex_agents_write` | `content` (required), `cwd` | object, `path` and `bytes` |
| `codex` | `prompt` (required), `model` | same object as `codex_exec` |

`codex_exec` parameters:

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

`POST /commands/codex_exec` with `{"prompt":"hi"}` returns `{"result": { ... }}`. A missing `prompt` is HTTP 400. A bad `sandbox` value or a non-zero `codex` exit is HTTP 500 `{"error","type"}`.

`codex_config_write` refuses `wire_api` other than `responses`, and refuses provider ids `openai`, `ollama`, and `lmstudio`. The file sets `supports_websockets = false` so a compatible endpoint is called over HTTPS.

When `codex_setup_check` reports `use_bypass: true`, `codex_exec` adds `--dangerously-bypass-approvals-and-sandbox`. That flag skips Codex's bubblewrap/seccomp sandbox and approval prompts. The Express container is the isolation boundary. When the probe succeeds, `sandbox=auto` uses `--sandbox workspace-write` and `approval_policy="never"`.

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
| `ABX_SERVER_TOKEN` | no | empty | When set, clients send `Authorization: Bearer`. |
| `ABX_SERVER_PORT` | no | `9000` | Port for a local `python3 commands.py`. |

Set secret values on `abx create --env` or `Sandbox.create(envs=...)`. Do not write them into the image.

`codex_exec` creates `config.toml` when a base URL is set and the file is missing. `codex_config_write` overwrites the file. Codex 0.162.1 will not send Chat Completions; `wire_api = "chat"` is a hard error.

## Resources

| Resource | Value |
|---|---|
| cpu | 2 vCPU |
| memory | 2048 MB |
| port | 9000 |
| disk | platform rootfs, about 10G on Express |

Long agent runs can use more memory than this request. The platform may ignore the memory field and apply its own size.

## Verified

No provider has a passing run recorded for this template.

## Secondary development

Bump the CLI in three places together: the `npm install -g @openai/codex@X.Y.Z` line in the Dockerfile, `PINNED_VERSION` in `commands.py`, and the `codex_version` smoke expect in `template.yaml`. Re-run `codex exec --help` before assuming flags. `--full-auto` and `--output-format` were already gone at 0.162.1.

Add a named command in `commands.py` with `@command`. Pass the upstream argv as a list. Keep `start()` under `if __name__ == "__main__"`.

To point Codex at another OpenAI-compatible Responses endpoint, call `codex_config_write` or set `OPENAI_BASE_URL` / `ABX_LLM_BASE_URL` before the first `codex_exec`. Put project rules in `AGENTS.md` via `codex_agents_write` or by writing the file under the workspace.

The nested sandbox probe is `sandbox_status()` in `commands.py`. Do not apt-install `bubblewrap` unless you have confirmed Codex will use that `bwrap`: the CLI prefers a `bwrap` on `PATH` over the bundled helper.

## Contributing

[CONTRIBUTING.md](../CONTRIBUTING.md) and [docs/template-spec.md](../docs/template-spec.md). Design notes: [docs/design/codex.md](../docs/design/codex.md).

## Issues

| Topic | Repository |
|---|---|
| This template, the spec, the checker | [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues) |
| Python SDK or `agent-sandbox-server` | [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), title prefix `[templates]` |
| `abx` CLI | [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues), title prefix `[templates]` |

## License

Apache-2.0, the same license as this repository. See [LICENSE](../LICENSE).
