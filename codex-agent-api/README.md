# codex-agent-api

## What it does

A project-defined HTTP session adapter that calls the official Codex CLI for every turn. The image pins `@openai/codex@0.162.1`, matching the [`codex`](../codex) template. It offers named commands and `/v1/agents/*` routes through `agent-sandbox-server` on port 9000. This is a limited session API; compatibility with every OpenAI Agents API feature or SDK method has not been established. Use the HTTP contract below rather than assuming a particular `client.beta.agents` interface exists.

Each turn uses `codex exec --json`. New sessions start a fresh Codex thread; later turns resume that exact thread id. A background monitor drains stdout and stderr concurrently, enforces a 300-second deadline even without a subscriber, and terminates the CLI process group on timeout, session deletion, or shutdown. Multiple subscribers read a bounded replay buffer rather than competing for stdout.

## Stack

Alibaba runtime base image `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>` (deployment defaults: `cn-hangzhou`, `v0.0.49`), Python 3.13, Node.js 20, Codex 0.162.1, and `agent-sandbox-server` pinned to python-sdk commit `e2cb27e24fde0a67112f82b8d44af463445a5d1a` in [Dockerfile](Dockerfile) (includes the dataclass command-loader fix). Runtime user: `user`. App: `/home/user/app`; workspace: `/home/user/workspace`. No image `CMD` or `ENTRYPOINT`.

## Problem solved

Provides HTTP session lifecycle, JSONL-to-SSE mapping, usage accounting and exact-thread resume around upstream Codex. It does not replace Codex's reasoning or tool execution. Sessions and saved agent configurations are in memory and disappear on server restart. All sessions share one workspace and one deployment identity; use a separate sandbox for mutually untrusted clients.

## Quick start (CLI)

Runtime configuration: the create-time key examples below require the named-command server to start with those values. For a prewarmed server, inspect its setup flags when provided and follow [explicit process configuration](../docs/runtime-environment.md); creating a sandbox does not reconfigure an already running server.

From the repository root, with existing provider configuration:

```bash
abx template deploy ./codex-agent-api -y --generation 2
abx create --template <template-id> -y
abx run <sandbox-id> codex_version
abx run <sandbox-id> agent_status
abx run <sandbox-id> codex --arg prompt='Reply with hello' --arg timeout_s=120
```

Inject the model provider's key and model into the sandbox creation environment through your secret mechanism. Do not place credentials in source files or shell history. `CODEX_SANDBOX=workspace-write` is the default. On Express, Linux user namespaces may be unavailable. Set `CODEX_SANDBOX=bypass` explicitly at creation only if the sandbox container supplies the required isolation. The adapter never changes that choice automatically.

## Quick start (Python SDK)

Use `agent-sandbox-client` (`agent_sandbox`), not the unrelated PyPI package `agent-sandbox`:

```python
import asyncio
import os
from agent_sandbox import Sandbox

async def main():
    runtime_env = {name: os.environ[name] for name in (
        "OPENAI_API_KEY", "CODEX_API_KEY", "ABX_LLM_API_KEY", "OPENAI_BASE_URL",
        "ABX_LLM_BASE_URL", "CODEX_MODEL", "CODEX_SANDBOX",
    ) if os.environ.get(name)}
    sb = await Sandbox.create(template="<template-id>", envs=runtime_env)
    try:
        print(await sb.run("codex_version"))
        result = await sb.run("codex", prompt="Reply with hello", timeout_s=120, timeout=150)
        print(result["status"])
    finally:
        await sb.kill()

asyncio.run(main())
```

Model calls require the provider environment described below. SDK named command calls return the command result directly.

## Quick start (HTTP POST)

Use the sandbox's authenticated port-9000 URL; retain the provider-required authentication headers. `ABX_SERVER_TOKEN`, when configured, adds `Authorization: Bearer <token>` at the server boundary.

```bash
curl -X POST "$SANDBOX_URL/commands/codex" \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"Reply with hello","model":"your-model","timeout_s":120}'

curl -X POST "$SANDBOX_URL/v1/agents/sessions" \
  -H 'Content-Type: application/json' \
  -d '{"agent":{"model":"your-model","instructions":"Be concise"},"input":"Reply with hello","background":true}'
curl "$SANDBOX_URL/v1/agents/sessions/<session-id>"
curl -N -X POST "$SANDBOX_URL/v1/agents/sessions/<session-id>/events" \
  -H 'Content-Type: application/json' \
  -d '{"input":"Continue","stream":true}'
```

Named commands return `{"result": ...}`. Session routes return their JSON directly, or SSE when `stream=true`. A JSON session response with `status=failed` is a failed model turn even if the HTTP status is 200. `background=true` returns immediately; poll the session until `status` is `idle`, `failed`, or `cancelled`. `stream` and `background` cannot both be true.

## Command reference

| Command | Parameters (type; required/default) | Result | Upstream argv |
|---|---|---|---|
| `codex_version` | None | Version string | `codex --version` |
| `agent_status` | None | JSON-encoded list of session id/status/model | None |
| `codex` | `prompt` str required; `model` str `""`; `timeout_s` int `300` (1–3600) | `{thread_id, events, status, events_truncated}`; failures raise RuntimeError | `codex exec --json --color never --skip-git-repo-check [provider/sandbox/model config] -- <prompt>` |

The service registers these project routes. Successful CRUD responses use HTTP 200. Missing objects: 404; invalid JSON parameters: 400; active-turn conflicts: 409; capacity: 429.

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

Input content arrays currently use their first `input_text` entry; this adapter does not implement image/audio inputs. Only URL-based MCP tools are supported: `{type:"mcp",server_label:"name",server_url:"https://host/mcp",headers:{...}}` (nested `transport` URL/headers are also accepted). Function tools, hosted connectors, approvals over HTTP, webhooks, durable storage and per-session filesystems are outside this contract. MCP configuration is passed to Codex using `-c mcp_servers.<label>.*`; secrets must remain in trusted deployment/runtime inputs.

Mapped SSE events include `agent.session.created`, `agent.session.turn.started`, `agent.session.turn.completed`, `agent.session.turn.failed`, `agent.session.output_item.added`, and `agent.session.output_item.done`. Unknown Codex event types use the `agent.session.<type>` prefix. `agent.session.events.truncated` signals that older replay events were dropped. Usage comes from upstream `turn.completed`, counted once regardless of subscriber count.

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
| `ABX_SERVER_PORT`, `ABX_SERVER_TOKEN` | `9000`, empty; server port/authentication |

The service retains at most 200 saved agent configurations; each session allows 100 turns. Replay and retained item buffers each hold at most 1000 events / 2 MB; a single JSONL line exceeding 256000 bytes fails the turn. stderr is drained continuously and only a bounded, redacted tail can be included in errors. Environment secret values, request-supplied MCP header values and bearer tokens are redacted from returned events/configurations/errors/text artifacts. Artifacts reject `.env`, `.aws`, `.codex`, `.ssh` paths and symlinks outside the workspace. This filtering supplements sandbox isolation; the standard shell/files APIs still require trusted access and server policy.

## Resources

2 vCPU, 4096 MB; one CLI per active session, up to the configured session capacity. Long model/tool calls count toward the turn deadline. No Docker daemon, KVM, privileged capability or second web server is required inside the sandbox.

## Verified

No provider has a passing run recorded for this template.

Local child-process regressions cover silent stdout deadlines, large stderr, process-group cleanup, background expiry, redaction, replay bounds, and subscriber accounting. Local HTTP smoke exercises CRUD and parameter rejection. `test_http_runtime.py` uses an explicitly synthetic CLI fixture to check real HTTP/background/SSE/cancellation and MCP header isolation; it does not certify upstream execution. Neither static review nor L0 establishes image/provider/model acceptance. The pinned binary's version/help were executed locally; no L1 image build or L2 provider deployment has passed in this resumed session.

```bash
python3 scripts/check_template.py codex-agent-api
python3 codex-agent-api/test_commands.py
python3 codex-agent-api/test_http_runtime.py
python3 -m pytest codex-agent-api/test_e2e_protocol.py -q
E2E_BASE_URL=http://127.0.0.1:9000 python3 codex-agent-api/e2e_test.py
# Real provider/model run, only with runtime credentials already configured:
E2E_REQUIRE_LLM=1 E2E_MODEL=your-model E2E_BASE_URL=https://your-sandbox \
  python3 codex-agent-api/e2e_test.py
```

The real coding checks upload a faulty existing `normalizer.py`, reproduce failures in six controller-owned tests via `/shell`, then require the background agent to fix that source and create `normalization-report.json`. The controller downloads the files, validates the report through both files and artifact APIs, and reruns the same six fixed tests to exit 0. These tests remain in the controller and are never uploaded as model-editable files. Exact-thread SSE resume must create a second artifact containing the actual report SHA-256 and output count, preserve the first source/report, and pass the fixed tests again. Agent messages `ABX_E2E_OK` and `ABX_RESUME_OK` alone cannot pass acceptance. `E2E_REQUIRE_LLM=1` forces execution and turns missing remote credentials, errors or disabled execution into failure; optional L0 without a model request reports SKIP. Set `E2E_TOKEN` (or `ABX_SERVER_TOKEN`) for server authentication, `E2E_WORKSPACE` to the server workspace when it differs from `/home/user/workspace`, and optionally `E2E_LLM_TIMEOUT` for controller polling. The harness deletes only its unique probe directory and session. Fake-remote protocol tests exercise the success branch and reject marker-only, incorrect report and incorrect resume output; they are not model/provider evidence. The pinned archive and an optional injected wheel both support `agent-sandbox-server serve --commands` with postponed-annotation dataclasses; when injecting a wheel, build it from the same fixed source commit.

## Express source-runtime verification

On 2026-10-16, the patched source passed 30 external HTTP checks on an owned Express base sandbox with pinned Codex 0.162.1 and a real Responses-compatible model. The production `serve --commands` startup loaded the dataclass-containing module. Acceptance repaired an existing broken source file, passed six controller-owned tests, verified a newly generated report, resumed the exact upstream thread, and independently checked the second artifact and report SHA-256. The owned sandbox was destroyed. [JSON evidence](evidence/runtime-express-2026-10-16.json) and [HTTP results](evidence/runtime-express-2026-10-16.log) include source/wheel provenance. This source-runtime result does not establish Dockerfile L1 or new-template deployment L2; `tested_on` remains empty. Reproduce with [the shared runner](../docs/express-source-runtime.md).

## Secondary development

Read [the design](../docs/design/codex-agent-api.md), [CONTRIBUTING](../CONTRIBUTING.md) and [template spec](../docs/template-spec.md). Extend the adapter around Codex's JSONL contract; do not implement a second agent loop. Keep the same CLI pin as `codex`. Official CLI reference: [OpenAI documentation](https://developers.openai.com/codex/cli/reference/).

## Contributing

Run the checker and local regressions before review. Include real L1/L2/L3 results and limitations in the PR; publish evidence only for passing provider runs. Never include `.env`, authentication headers, secret values, or generated credential/config files.

## Issues

[Template issue #23](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/23). SDK/server defects belong in [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues); CLI/deploy defects belong in [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues), with `[templates]` title prefix.

## License

Apache-2.0. Codex and dependencies retain their respective upstream licenses.
