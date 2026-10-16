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

From this repository with the required provider build credentials:

```bash
abx template deploy ./agents-cli -y
abx create --template <template-id> -y
abx run <sandbox-id> agents_version
```

The result is `codex 0.162.1; qwen-code 0.23.0`. Create a sandbox with compatible
credentials before submitting a model turn, for example `--env
OPENAI_API_KEY=<compatible-key>` and the base URL/model configuration that your
selected CLI requires. Do not include credentials in images or checked-in files.

```bash
abx kill <sandbox-id> -y
abx template delete <template-id> -y
```

## Quick start (Python SDK)

Install `agent-sandbox-client` using the [paired pinned source instructions](../docs/python-client-installation.md)
until the matching package is published. The import is `agent_sandbox`.

```python
import asyncio
from agent_sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=300)
    try:
        print(await sb.run("agents_version", timeout=60))
        print(sb.network.get_url(9000))
    finally:
        await sb.kill()

asyncio.run(main())
```

If the sandbox was created with `ABX_SERVER_TOKEN`, pass the matching server credential with
`await sb.server_at(9000, token="<server-token>").commands.run("agents_version", timeout=60)`.

The named diagnostic returns a buffered string. Use the HTTP session routes below
for turns. General SDK files/process operations receive HTTP 404 under this policy.

## Quick start (HTTP POST)

Use the sandbox's port-9000 URL. Add the provider's gateway access header when
required, independently of the optional server token:

```bash
curl --fail-with-body --request POST "$ABX_SERVER_URL/commands/agents_version" \
  --header "Content-Type: application/json" \
  --header "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --data '{}'
```

The direct argument object has no `args` wrapper. HTTP 200 returns
`{"result":"codex 0.162.1; qwen-code 0.23.0"}`. Server authentication uses
`ABX_SERVER_TOKEN` with Bearer or `X-Access-Token`; when a gateway also requires
`X-Access-Token`, put the server token in Bearer. `/health` is public.

A model session uses an explicit runtime and an existing target workspace:

```bash
curl --fail-with-body "$ABX_SERVER_URL/v1/agents/sessions" \
  --header "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --header "Content-Type: application/json" \
  --data '{"adapter":"qwen-code","agent":{"model":"<compatible-model>"},"environment":{"type":"self_hosted","workspace_directory":"/home/user/workspace"}}'
```

The session response contains `id`. Send a turn, then poll items:

```bash
curl --fail-with-body "$ABX_SERVER_URL/v1/agents/sessions/<id>/events" \
  --header "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --header "Content-Type: application/json" \
  --data '{"events":[{"type":"agent.session.input.message","input":[{"role":"user","content":[{"type":"input_text","text":"Describe this workspace."}]}]}]}'
curl --fail-with-body "$ABX_SERVER_URL/v1/agents/sessions/<id>/items?limit=100&order=asc" \
  --header "Authorization: Bearer $ABX_SERVER_TOKEN"
```

Event submission returns 202 before model completion. HTTP 400 means invalid
arguments, 401 missing/incorrect server authentication, 404 an unknown or disabled
route/runtime/session, and 500 a diagnostic execution failure. Model-turn failures
are reported in session/items state; accepting an event does not prove the model
turn succeeded. An HTTP timeout does not cancel an upstream turn.

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
| `ABX_SERVER_TOKEN` | Recommended for exposed endpoints | Server API authentication, declared empty |
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

No provider has a passing run recorded for this template.

Local real-CLI diagnostics and HTTP contract checks are separate from fixture
protocol tests. Neither establishes image deployment or actual model/coding
acceptance. L1/L2 and artifact-based real-model L3 remain required.

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
The Dockerfile does not copy those fixtures. Default e2e requires actual installed
CLIs and submits no model turn. `E2E_REQUIRE_LLM=1` or `E2E_RUN_LLM=1` exits nonzero
because this restricted API suite has no out-of-band artifact verifier. Do not
count protocol markers as L3. Add a separate verifier that independently inspects
changed source, new artifacts and tests before claiming genuine coding acceptance.

## Contributing

Read [CONTRIBUTING.md](../CONTRIBUTING.md), the [template spec](../docs/template-spec.md)
and [design](../docs/design/agents-cli.md). Track this work in [Issue #25](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/25).

## Issues

Template/policy integration: [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues).
Runtime/API defects: [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues).
CLI deployment defects: [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).

## License

Apache-2.0; see [LICENSE](../LICENSE). Upstream CLIs retain their own licenses.
