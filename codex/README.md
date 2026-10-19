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

Check the installed entry with `abx create --help`. The complete example below uses native CLI syntax. If help lists `--detach`, use the standard Express entry: create with `abx create <template-id> --detach` and clean up with `abx kill <sandbox-id>` without `-y`; named commands through `abx run` are unchanged. See the [entry comparison](../docs/using-templates.md#client-entry-compatibility).

Runtime configuration: the create-time key examples below require the named-command server to start with those values. For a prewarmed server, inspect its setup flags when provided and follow [explicit process configuration](../docs/runtime-environment.md); creating a sandbox does not reconfigure an already running server.

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

The client distribution is `agent-sandbox-client` (import `agent_sandbox`). Until the matching release is available, use the [paired, pinned source installation](../docs/python-client-installation.md).

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox

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

`await sb.run("codex_exec", prompt="...")` returns the result object (`last_message`, `events`, `thread_id`). `sb.commands.run` is the shell API; use the async `Sandbox.create` example above for sandbox lifecycle management.

Resume with the `thread_id` from the first result:

```python
await sb.run("codex_exec", prompt="Continue.", resume="<thread_id>")
```

## Quick start (HTTP POST)

For a server reachable at `http://127.0.0.1:9000` (for example a local template process):

```bash
curl --fail-with-body -X POST http://127.0.0.1:9000/commands/codex_exec \
  -H 'Content-Type: application/json' \
  --data '{"prompt":"Summarize the workspace.","sandbox":"read-only","approval":"never","json_events":true,"timeout_s":120}'
```

Use the sandbox gateway URL from `sb.network.get_url(9000)` for a remote sandbox and the gateway's required authentication. When the application has `ABX_SERVER_TOKEN` configured, send its bearer token in the authorization header using your application's secret handling. The response wraps the command result in `{"result": ...}`; tool events and stderr redact known secret environment values.

A successful execution is HTTP 200 with `{"result":{"last_message":"...","events":[],"thread_id":"..."}}`. Missing or mistyped required arguments produce HTTP 400; failed application authentication produces HTTP 401. Invalid sandbox policy or upstream execution failure produces HTTP 500 with `{"error":"...","type":"RuntimeError"}` (or `ValueError` for invalid values).

`timeout_s` defaults to 300 and accepts integers from 1 to 3600. Set your HTTP read timeout above that value, including server and gateway overhead. A client or gateway timeout can happen before the server finishes; it does not confirm that the child process stopped. A server-side Codex timeout is reported as HTTP 500. Named commands return one complete JSON response, so use the process API for live output.

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

`sandbox=auto` uses `workspace-write` when the probe succeeds and falls back to `--dangerously-bypass-approvals-and-sandbox` when it fails. `sandbox=bypass` explicitly selects that flag. It skips Codex's bubblewrap/seccomp sandbox and approval prompts; isolation then comes from the Express container. An explicit `read-only`, `workspace-write`, or `danger-full-access` request is rejected when the Linux sandbox probe fails, before workspace, git, provider config, or `AGENTS.md` writes. Explicit requests never silently become bypass. The probe itself may create its isolated `sandbox-probe` state directory.

`codex_config_write` accepts `base_url` (default `ABX_LLM_BASE_URL`, then `OPENAI_BASE_URL`), `provider` (default `compatible`), `env_key` (a variable name), `model`, `wire_api` (only `responses`), and `codex_home` (default `CODEX_HOME` or `~/.codex`). It overwrites `config.toml` with mode `0600`. `codex_agents_write` accepts required `content` and optional `cwd`; it overwrites `cwd/AGENTS.md`.

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

## Runtime verification

On 2026-10-16, patched command source with pinned Codex 0.162.1 passed a real
model coding task on `alicloud-express`: remote code/artifact retrieval, independent
Fibonacci assertions, and a separate unittest run. All 16 HTTP checks passed, and
the owned sandbox was deleted. The source and runtime package hashes are in
[evidence](evidence/runtime-express-2026-10-16.json), with the [check log](evidence/runtime-express-2026-10-16.log).
This used an existing platform base sandbox with runtime-installed dependencies;
that source-only run did not verify the Dockerfile image or new-template deployment.

A later reviewed-image run used the hardened public controller at `06071e4` and
passed 17 real-model HTTP checks without failures or skips. It verified an existing
source correction, unchanged original tests, exact artifacts and trusted independent
test completion. Its owned sandbox and officially registered template were confirmed
absent afterward; the shared image registry remains owned by the ongoing review batch.
See the [sanitized image evidence](evidence/image-runtime-hardened-2026-10-16.json).
The full `abx template deploy` runner remains unrun; this is supplemental component evidence.

## Verified

| Provider | Executed scope | Evidence |
| --- | --- | --- |
| alicloud-express | steps build, official READY, CLI + SDK smoke, independent owned cleanup readback | [2026-10-19](evidence/express-2026-10-19.json) |

This run uses the pinned e2cb27e server-source override matching existing image CI injection; the receipt records exact versions, input hashes and build mode. Only verification metadata changes here; the template stays experimental. Dockerfile L1, full product and real-model acceptance are assessed by their separate records and cannot be inferred from basic smoke.

<details>
<summary>Earlier checkpoint text (historical; current steps result is above)</summary>

No provider has a passing canonical deployment receipt recorded for this template.

</details>

## Secondary development

Bump the CLI in three places together: the `npm install -g @openai/codex@X.Y.Z` line in the Dockerfile, `PINNED_VERSION` in `commands.py`, and the `codex_version` smoke expect in `template.yaml`. Re-run `codex exec --help` before assuming flags. `--full-auto` and `--output-format` were already gone at 0.162.1.

Add a named command in `commands.py` with `@command`. Pass the upstream argv as a list. Keep `start()` under `if __name__ == "__main__"`.

To point Codex at another OpenAI-compatible Responses endpoint, call `codex_config_write` or set `OPENAI_BASE_URL` / `ABX_LLM_BASE_URL` before the first `codex_exec`. Put project rules in `AGENTS.md` via `codex_agents_write` or by writing the file under the workspace.

The nested sandbox probe is `sandbox_status()` in `commands.py`. Do not apt-install `bubblewrap` unless you have confirmed Codex will use that `bwrap`: the CLI prefers a `bwrap` on `PATH` over the bundled helper.

### Agent Sandbox platform steps

From a repository checkout, `python scripts/run_steps_e2e.py codex` builds and verifies this template through real Express platform steps. See [preparation, credentials, exact build provenance and cleanup](../docs/platform-steps.md). A model-free step smoke does not establish L3.

## Contributing

[CONTRIBUTING.md](../CONTRIBUTING.md) and [docs/template-spec.md](../docs/template-spec.md). Design notes: [docs/design/codex.md](../docs/design/codex.md).

From the repository root, run `python3 -m unittest discover -s codex -p test_commands.py -v`, `python3 scripts/check_template.py codex`, and `python3 scripts/run_local_e2e.py`. The unit suite checks explicit permissions, automatic fallback, result redaction, and false agent-success markers. L0 checks HTTP command contracts and may skip the model task; it does not establish L1 image builds, L2 cloud execution, or L3 agent acceptance.

For L3 against a local or remote template server, run `E2E_BASE_URL=http://127.0.0.1:9000 E2E_RUN_LLM=1 E2E_REQUIRE_LLM=1 E2E_MODEL=<model> python3 codex/e2e_test.py` with authorized model configuration already supplied to both processes. The controller seeds an incorrect existing Fibonacci implementation and original tests, and verifies the expected failing baseline. The agent must fix that implementation, preserve the original tests byte for byte, add unittest coverage and `REPORT.md`, execute a command successfully, and write exact `acceptance.txt` content. The test requires the final assistant marker, checks the changed source and artifacts, independently asserts Fibonacci results and negative-input rejection, and reruns both the original and generated tests. The independent verifiers use isolated Python, compile actual source bytes, require complete successful test results, and require fresh completion acknowledgements chosen after the agent exits. Early process exit, skipped or expected-failing tests, shadowed unittest modules and stale bytecode cannot supply a passing receipt. This checks completion; it is not an isolation boundary against hostile code with the same operating-system authority. A chat reply or an echoed marker in tool events fails. Artifact reads use the remote files API, and independent assertions/tests run through the remote shell API. Set `E2E_WORKSPACE` to a writable directory inside the server file root (default `/home/user/workspace`) and `E2E_TOKEN` if the server requires authentication. Each run uses a unique directory and deletes only that directory. Record only actual passing provider evidence, and report model skips separately.

## Issues

| Topic | Repository |
|---|---|
| This template, the spec, the checker | [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues) |
| Python SDK or `agent-sandbox-server` | [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), title prefix `[templates]` |
| `abx` CLI | [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues), title prefix `[templates]` |

## License

Apache-2.0, the same license as this repository. See [LICENSE](../LICENSE).
