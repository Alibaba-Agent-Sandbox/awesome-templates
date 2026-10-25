# codex-agent-api

## What it does

A project-defined HTTP session adapter that calls the official Codex CLI for every turn. The image pins `@openai/codex@0.162.1`, matching the [`codex`](../codex) template. It offers named commands and `/v1/agents/*` routes through `agent-sandbox-server` on port 9000. This is a limited session API; compatibility with every OpenAI Agents API feature or SDK method has not been established. Use the HTTP contract below rather than assuming a particular `client.beta.agents` interface exists.

Each turn uses `codex exec --json`. New sessions start a fresh Codex thread; later turns resume that exact thread id. A background monitor drains stdout and stderr concurrently, enforces a 300-second deadline even without a subscriber, and terminates the CLI process group on timeout, session deletion, or shutdown. Multiple subscribers read a bounded replay buffer rather than competing for stdout.

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a2`, installed directly by the Dockerfile.

Alibaba runtime base image `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>` (deployment defaults: `cn-hangzhou`, `v0.0.49`), Python 3.13, Node.js 20, Codex 0.162.1, and `agent-sandbox-server` pinned to python-sdk commit `e2cb27e24fde0a67112f82b8d44af463445a5d1a` in [Dockerfile](Dockerfile) (includes the dataclass command-loader fix). Runtime user: `user`. App: `/home/user/app`; workspace: `/home/user/workspace`. No image `CMD` or `ENTRYPOINT`.

## Problem solved

Provides HTTP session lifecycle, JSONL-to-SSE mapping, usage accounting and exact-thread resume around upstream Codex. It does not replace Codex's reasoning or tool execution. Sessions and saved agent configurations are in memory and disappear on server restart. All sessions share one workspace and one deployment identity; use a separate sandbox for mutually untrusted clients.

## Quick start (CLI)

Follow the [usage guide](../docs/using-templates.md#installation) to install the clients, configure the provider and set an independent `ABX_SERVER_TOKEN`. From this repository's root, launch the application and retain its sandbox ID. Replace `<sandbox-id>` below with that ID.

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./codex-agent-api --yes
abx run <sandbox-id> codex_version --json-args '{}'
```

`template launch` prepares and starts this instance's application. For OpenSandbox, set `ABX_PROVIDER=opensandbox` above and use `provider="opensandbox"` in Python. See the [complete calling flow](../docs/using-templates.md#cli-sdk-and-http) for OpenSandbox configuration, provider selection on every call and owned-resource cleanup. The next examples reuse the same running instance.

## Quick start (Python SDK)

Install `agent-sandbox-client` and follow the [Python connection example](../docs/using-templates.md#cli-sdk-and-http), using `ProviderSandbox.connect` and `application_client` with the independent application token. Replace the command call inside that example's `try` block with:

```python
print(await client.commands.run('codex_version'))
```

Keep the guide's connection and close steps. `sb.commands.run` executes a process; `client.commands.run` calls this template's named commands. Business commands, arguments and limits are listed in the command reference below.

## Quick start (HTTP POST)

Follow the [HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserve gateway headers, path and query parameters, and set the independent application token. Change the request to `POST /commands/codex_version`, with `Content-Type: application/json` and this direct argument object:

```json
{}
```

Expected response for this check:

```json
{"result": "0.162.1"}
```

`result` is buffered, not an event stream. Missing or mistyped arguments return 400, failed authentication 401, unknown commands 404, and execution errors 500. Set the HTTP wait and command deadline separately; a client timeout does not guarantee cancellation.

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
| `ABX_SERVER_PORT` | `9000`; server port |
| `ABX_SERVER_TOKEN` | Export an independent application token before the application workflow launch; separate from model and gateway credentials |

The service retains at most 200 saved agent configurations; each session allows 100 turns. Replay and retained item buffers each hold at most 1000 events / 2 MB; a single JSONL line exceeding 256000 bytes fails the turn. stderr is drained continuously and only a bounded, redacted tail can be included in errors. Environment secret values, request-supplied MCP header values and bearer tokens are redacted from returned events/configurations/errors/text artifacts. Artifacts reject `.env`, `.aws`, `.codex`, `.ssh` paths and symlinks outside the workspace. This filtering supplements sandbox isolation; the standard shell/files APIs still require trusted access and server policy.

## Resources

2 vCPU, 4096 MB; one CLI per active session, up to the configured session capacity. Long model/tool calls count toward the turn deadline. No Docker daemon, KVM, privileged capability or second web server is required inside the sandbox.

## Verified

See [test results and scope](../docs/using-templates.md#evidence-and-providers). The dated records below identify the tested input and entry point.

## Express source-runtime verification

On 2026-10-16, the patched source passed 30 external HTTP checks on an owned Express base sandbox with pinned Codex 0.162.1 and a real Responses-compatible model. The production `serve --commands` startup loaded the dataclass-containing module. Acceptance repaired an existing broken source file, passed six controller-owned tests, verified a newly generated report, resumed the exact upstream thread, and independently checked the second artifact and report SHA-256. The owned sandbox was destroyed. [JSON evidence](evidence/runtime-express-2026-10-16.json) and [HTTP results](evidence/runtime-express-2026-10-16.log) include source/wheel provenance. That historical source-runtime receipt alone does not establish Dockerfile L1 or new-template L2; current canonical qualification is recorded above. Reproduce with [the shared runner](../docs/express-source-runtime.md).


The fixed-test reruns also require a fresh controller-only completion ACK emitted after all six tests genuinely complete with no skips/expected failures. Forged `Ran 6 tests`/`OK` text followed by an early exit cannot pass. This checks ordinary test completion; it is not an isolation boundary against hostile same-user code. `ABX_SERVER_TOKEN` supplies the application Bearer credential; `E2E_GATEWAY_HEADERS_JSON` carries the distinct provider gateway headers.

## Secondary development

Read [the design](../docs/design/codex-agent-api.md), [CONTRIBUTING](../CONTRIBUTING.md) and [template spec](../docs/template-spec.md). Extend the adapter around Codex's JSONL contract; do not implement a second agent loop. Keep the same CLI pin as `codex`. Official CLI reference: [OpenAI documentation](https://developers.openai.com/codex/cli/reference/).

### Agent Sandbox platform steps

From a repository checkout, `python scripts/run_steps_e2e.py codex-agent-api` builds and verifies this template through real Express platform steps. See [preparation, credentials, exact build provenance and cleanup](../docs/platform-steps.md). A model-free step smoke does not establish L3.

## Contributing

Run the checker and local regressions before review. Include real L1/L2/L3 results and limitations in the PR; publish evidence only for passing provider runs. Never include `.env`, authentication headers, secret values, or generated credential/config files.

## Issues

[Template issue #23](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/23). SDK/server defects belong in [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues); CLI/deploy defects belong in [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues), with `[templates]` title prefix.

## License

Apache-2.0. Codex and dependencies retain their respective upstream licenses.

### 2026-10-20 full step checkpoint: template2.0.0

[Real current-version steps](evidence/express-2026-10-20.json) and [complete external HTTP controller](evidence/verification-steps-2026-10-20T154830Z.json): official READY, actual Python SDK creation, all CLI/SDK smoke and 18 PASS/0 FAIL/1 SKIP; independent owned sandbox/template cleanup passed. Model acceptance remains NOT_RUN in this receipt; it does not relabel earlier image/model scope. Reproduction and exact server/controller provenance: [step guide](../docs/platform-steps.md).
