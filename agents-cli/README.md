# agents-cli

Pinned Codex and Qwen Code behind a restricted local Agents HTTP API.

## What it does

Installs `@openai/codex@0.162.1` and `@qwen-code/qwen-code@0.23.0`. The server
exposes a version diagnostic and six session/runtime routes. Callers create a
session, submit messages and poll its items. `X-Agent-Sandbox-Local: 1` labels the
local Agents implementation; it does not mean an OpenAI hosted Agents service.

Both direct startup and the configured `agent-sandbox-server serve` command load
[server-policy.json](./server-policy.json). Shell, files, generic process APIs,
model listing and all other Agents routes are disabled. The agent subprocess
still has its configured workspace permissions; closing HTTP file/shell routes
does not remove the upstream CLI's tools.

## Stack

- Alibaba generation-2 base image and its Python; SHA256-verified official Node.js `24.16.0` replaces the base Node 20 to satisfy Qwen Code's Node >=22 requirement.
- Codex CLI `0.162.1`, Qwen Code CLI `0.23.0`; image build asserts both versions.
- `agent-sandbox-server` pinned to python-sdk commit
  `e2cb27e24fde0a67112f82b8d44af463445a5d1a`, or a supplied source-built wheel.
- Non-root `user`, app `/home/user/app`, workspace `/home/user/workspace`, port 9000.

## Problem solved

Provides one HTTP session surface for selecting either installed coding CLI while
keeping the general sandbox shell/files surface closed. Diagnostic checks run the
actual CLIs; disabling model tests never substitutes synthetic programs.

## Quick start (CLI)

Follow the [usage guide](../docs/using-templates.md#installation) to install the clients, configure the provider and set an independent `ABX_SERVER_TOKEN`. From this repository's root, launch the application and retain its sandbox ID. Replace `<sandbox-id>` below with that ID.

```bash
abx --provider alicloud-express template launch ./agents-cli --workflow application --yes
abx run <sandbox-id> agents_version --json-args '{}'
```

`template launch` prepares and starts this instance's application. See the [complete calling flow](../docs/using-templates.md#cli-sdk-and-http) for OpenSandbox configuration, provider selection on every call and owned-resource cleanup. The next examples reuse the same running instance.

## Quick start (Python SDK)

Install `agent-sandbox-client` and follow the [Python connection example](../docs/using-templates.md#cli-sdk-and-http), using `ProviderSandbox.connect` and `application_client` with the independent application token. Replace the command call inside that example's `try` block with:

```python
print(await client.commands.run('agents_version'))
```

Keep the guide's connection and close steps. `sb.commands.run` executes a process; `client.commands.run` calls this template's named commands. Business commands, arguments and limits are listed in the command reference below.

## Quick start (HTTP POST)

Follow the [HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserve gateway headers, path and query parameters, and set the independent application token. Change the request to `POST /commands/agents_version`, with `Content-Type: application/json` and this direct argument object:

```json
{}
```

Expected response for this check:

```json
{"result": "codex 0.162.1; qwen-code 0.23.0"}
```

`result` is buffered, not an event stream. Missing or mistyped arguments return 400, failed authentication 401, unknown commands 404, and execution errors 500. Set the HTTP wait and command deadline separately; a client timeout does not guarantee cancellation.

## Command reference

| Command | Parameters | Returns | Execution |
|---|---|---|---|
| `agents_version` | None; `{}` | Buffered string | Actual `codex --version` and `qwen --version`, each with a 20-second deadline; missing/wrong version raises an error without raw CLI output. |

| Enabled route | Purpose |
|---|---|
| `GET /commands`, `POST /commands/agents_version` | Discover/run the diagnostic |
| `POST /v1/agents/sessions` | Create a session; `adapter` selects `codex` or `qwen-code`; the default runtime is Codex |
| `GET /v1/agents/sessions`, `GET /v1/agents/sessions/{id}` | List/reconnect sessions |
| `POST /v1/agents/sessions/{id}/events` | Queue messages |
| `GET /v1/agents/sessions/{id}/items` | Poll output items |
| `GET /v1/agents/runtimes` | Inspect declared, implemented and installed runtimes |

Session records and output are process-local and are lost when this server is
restarted. Delete/cancel/update/SSE and generic shell/files routes are outside this
allowlist. Destroy an owned sandbox to end its server and resources.

## Configuration

| Name | Required | Purpose |
|---|---|---|
| `ABX_SERVER_TOKEN` | Required; empty manifest declaration | Export the independent application token before launch |
| `OPENAI_API_KEY` | For compatible model turns | Runtime credential, declared empty; usable by Qwen and compatible Codex setups |
| `CODEX_API_KEY` | Optional Codex alternative | Declared empty; actual authentication support depends on the chosen upstream provider |
| `OPENAI_BASE_URL`, `OPENAI_MODEL` | Provider-dependent | Qwen's compatible endpoint/model configuration |
| `CODEX_HOME` | No | Codex state directory, `/home/user/.codex` |
| `WORKSPACE` | No | `/home/user/workspace`; session requests should specify the target workspace explicitly |
| `ABX_SERVER_POLICY_FILE` | Set in image | Path to the shipped policy; the canonical start command also passes `--policy` explicitly |

Changing the policy deliberately changes the public HTTP surface. Keep the shipped
allowlist for this template's documented contract. `E2E_RUN_LLM=0` controls tests
only and never rewrites production PATH or installs fixtures.

## Resources

2 vCPU, 4096 MB RAM, port 9000. Express has about 10 GB rootfs. Model/tool workload
memory and latency have not been measured; no image-size acceptance is claimed.

## Verified

See [test results and scope](../docs/using-templates.md#evidence-and-providers). The dated records below identify the tested input and entry point.

## Historical verification

| Provider | Executed scope | Evidence |
| --- | --- | --- |
| alicloud-express | steps build, official READY, CLI + SDK smoke, independent owned cleanup readback | [2026-10-19](evidence/express-2026-10-19.json) |

This run uses the pinned e2cb27e server-source override matching existing image CI injection; the receipt records exact versions, input hashes and build mode. Only verification metadata changes here; the template stays experimental. Dockerfile L1, full product and real-model acceptance are assessed by their separate records and cannot be inferred from basic smoke.

## Secondary development

Keep both version pins in Dockerfile, `commands.py`, smoke metadata and fixtures
consistent. From the repository root:

```bash
python -m pytest --import-mode=importlib -q agents-cli/test_protocol.py
python scripts/check_template.py agents-cli
python scripts/run_local_e2e.py
```

Protocol tests explicitly put `e2e-bin` on only their child process PATH and test
both startup forms, authentication, disabled routes and two turns of each adapter.
The Dockerfile does not copy those fixtures. Default HTTP e2e requires actual
installed CLIs and submits no model turn. `E2E_REQUIRE_LLM=1` or `E2E_RUN_LLM=1`
still exits nonzero and directs callers to `e2e_sdk.py`. It never trusts an external
receipt or arbitrary verifier hook. Run
`python -m pytest --import-mode=importlib -q agents-cli/test_sdk_verifier.py` for
no-network negative controls; those are separate from actual model/provider runs.

### Agent Sandbox platform steps

From a repository checkout, `python scripts/run_steps_e2e.py agents-cli` builds and verifies this template through real Express platform steps. See [preparation, credentials, exact build provenance and cleanup](../docs/platform-steps.md). A model-free step smoke does not establish L3.

## Contributing

Read [CONTRIBUTING.md](../CONTRIBUTING.md), the [template spec](../docs/template-spec.md)
and [design](../docs/design/agents-cli.md). Track this work in [Issue #25](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/25).

## Issues

Template/policy integration: [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues).
Runtime/API defects: [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues).
CLI deployment defects: [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).

## License

Apache-2.0; see [LICENSE](../LICENSE). Upstream CLIs retain their own licenses.

### 2026-10-20 full step checkpoint: template2.0.1

[Real current-version steps](evidence/express-2026-10-20.json) and [complete external HTTP controller](evidence/verification-steps-2026-10-20T154625Z.json): official READY, actual Python SDK creation, all CLI/SDK smoke and 18 PASS/0 FAIL/1 SKIP; independent owned sandbox/template cleanup passed. Model acceptance remains NOT_RUN in this receipt; it does not relabel earlier image/model scope. Reproduction and exact server/controller provenance: [step guide](../docs/platform-steps.md).
