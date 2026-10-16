# codex-agent-api

## Purpose

Expose an HTTP session lifecycle for trusted users who need upstream Codex turns, SSE events and exact-thread continuation inside an Agent Sandbox. Issue #23 tracks this template. The API is a documented project subset, with no assertion of complete compatibility with an external OpenAI SDK/API.

## Capabilities

Named commands plus saved-agent/session CRUD, bounded background turns, multi-subscriber event replay, usage accounting and text artifacts. Reasoning and tool execution remain entirely in `@openai/codex@0.162.1`, matching the separate `codex` template. The server never runs a second model-agent implementation. All sessions share one container filesystem and deployment identity. MCP is limited to URL-based servers; HTTP function tools, hosted connectors, approvals, webhooks and persistent storage are unsupported.

## Exposed API

| Command | Parameters | Return | Executed argv |
|---|---|---|---|
| `codex_version` | None | `str` CLI version | `codex --version` |
| `agent_status` | None | JSON string of `{id,status,model}` list | None |
| `codex` | `prompt: str` required; `model: str=""`; `timeout_s: int=300`, range 1–3600 | `{thread_id,events,status}`; failure raises RuntimeError | `codex exec --json --color never --skip-git-repo-check [sandbox/model/provider config] -- PROMPT` |

The same server owns `/v1/agents` CRUD and `/v1/agents/sessions` CRUD plus events/items/artifacts. [English](../../codex-agent-api/README.md#command-reference) and [Chinese](../../codex-agent-api/README.zh-CN.md#命令参考) list every method, POST parameter, type and default. Session `background=true` immediately returns state; polling reports actual terminal success or failure. `stream=true` returns SSE; the two cannot both be true. A failed turn is never synthesized as `turn.completed` even on zero CLI exit. Subsequent turns require the exact captured `thread_id`, never global `resume --last`. Instructions use the upstream `developer_instructions` config key.

One monitor per process starts immediately, uses a selector to drain both pipes, checks a monotonic deadline independent of stdout or subscriber progress, and broadcasts redacted events. The monitor alone updates usage and state; HTTP consumers never compete for process stdout or duplicate accounting. Replay and item buffers cap count at 1000 and bytes at 2 MB; oversized JSONL lines fail at 256000 bytes. stderr retains a bounded tail plus secret overlap, redacts before final truncation, and is never printed raw. Disconnects leave a bounded background turn; session deletion/TTL/deadline/normal exit terminate the whole dedicated CLI process group. Sessions cap at 100 turns.

## How to build

Use [Dockerfile](../../codex-agent-api/Dockerfile): Alibaba runtime base with deployment-resolved region/tag (`cn-hangzhou`, `v0.0.49` defaults), Codex 0.162.1 npm pin/cache cleanup, and python-sdk archive fallback pinned to `e2cb27e24fde0a67112f82b8d44af463445a5d1a` (includes the dataclass loader fix). The image uses `WORKDIR /home/user/app`, `USER user`, `WORKSPACE=/home/user/workspace` and `CODEX_HOME=/home/user/.codex`. No `CMD`/`ENTRYPOINT` override. The fallback includes `sys.modules` registration for dynamically imported dataclasses with postponed annotations; an optional injected wheel should use the same fixed source commit.

`generation: 2`; `start_cmd`: `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`; `ready_cmd`: `agent-sandbox-server healthcheck --port 9000`. `commands.py` is copied after dependency installation. The pinned source fallback works without an injected wheel; deployment may inject a wheel built from the same source commit. No OpenAI Python SDK package is needed by the server.

## Express feasibility

Feasible: yes

Limiting factor: the runtime's ability to execute Codex's Linux sandbox, plus provider/model authorization.

The HTTP adapter and upstream CLI require neither Docker nor KVM inside Express. Default `CODEX_SANDBOX=workspace-write` preserves the CLI isolation request. Some Express containers cannot start Linux user namespaces; container isolation with `CODEX_SANDBOX=bypass` is an explicit deployment decision and is never automatic. 2 vCPU, 4096 MB, non-root `user` suffice for the bounded service design; actual image deployment and provider acceptance remain unverified.

## Risks

Runtime model calls and MCP requests use network access. Keys are injected through runtime environment and never baked into the image. API bodies/errors/configurations and events redact secret environment values/bearer tokens; text artifacts also redact those values. Artifact paths resolve symlinks before workspace checks, refuse secret-directory names and cap downloads at 1 MB. Config/auth storage remains outside the workspace. Standard process/file APIs still need trusted caller authorization and server policy. This is not per-session tenant isolation. In-memory state/replay is ephemeral and can truncate; 100 turns/session and session capacity bound retention. No credentials, `.env`, generated auth files or failed provider evidence enter commits.

## Test plan

L0: `python3 scripts/check_template.py codex-agent-api`; `python3 codex-agent-api/test_commands.py`; `python3 codex-agent-api/test_http_runtime.py` (explicit synthetic CLI fixture, actual HTTP/child processes); local server plus `E2E_BASE_URL=... python3 codex-agent-api/e2e_test.py`. Actual subprocess regressions must demonstrate silent stdout deadline, large-stderr draining, tool descendant termination, background expiry, multi-subscriber accounting, synthetic secret redaction, event size/replay bounds and failure when upstream emits `turn.failed` or exits without completion. HTTP smoke covers saved-agent/session CRUD, invalid input/tool rejection and artifact secret-path denial.

L1: build the Alibaba-based image; confirm `codex-cli 0.162.1` from inside the image and successful `serve --commands` with the fixed SDK archive or corresponding injected wheel. Local npm binary version/help alone do not establish L1.

L2: `python3 scripts/express_e2e.py codex-agent-api`; smoke `codex_version == "0.162.1"` and `agent_status == "[]"` through CLI and SDK. Save provider evidence only on complete pass. No L2 pass is currently recorded.

L3: with authorized remote runtime model configuration, `E2E_REQUIRE_LLM=1 E2E_MODEL=... E2E_BASE_URL=... python3 codex-agent-api/e2e_test.py` seeds a faulty existing `normalizer.py` through files API, proves six fixed tests fail through `/shell`, then runs a real background Codex coding task. The source must change, a new JSON report must match expected data through independent files/artifact reads, actual upstream command-tool completion must be recorded, and those same six tests must pass remotely. Fixed test code remains in the controller and is passed only to shell execution, never stored in model-editable files. Exact-thread SSE resume must create a SHA-256/count summary artifact, preserve the repaired source/first report and pass the six tests again. Markers alone do not pass. `E2E_REQUIRE_LLM=1` forces non-skipping behavior; remote missing authorization, timeouts, wrong output or errors fail. `E2E_TOKEN` takes precedence over `ABX_SERVER_TOKEN`; `E2E_WORKSPACE` must match the service workspace. Cleanup deletes only the unique owned session/project. `test_e2e_protocol.py` uses fake remote responses but real test subprocesses to cover success and reject marker-only/wrong-report/wrong-resume; those are harness regressions, not provider/model evidence. No L4 provider is planned beyond Express at this stage.
