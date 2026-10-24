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

The examples use the current Express CLI: `abx create <template-id> --detach` prints the sandbox ID; `abx kill <sandbox-id>` cleans it up. Named commands use `abx run`. See the [entry comparison](../docs/using-templates.md#client-entry-compatibility).

Runtime configuration: the create-time key examples below require the named-command server to start with those values. For a prewarmed server, inspect its setup flags when provided and follow [explicit process configuration](../docs/runtime-environment.md); creating a sandbox does not reconfigure an already running server.

From this repository with the required provider build credentials:

```bash
abx template deploy ./agents-cli -y
abx create <template-id> --detach
abx run <sandbox-id> agents_version
```

The result is `codex 0.162.1; qwen-code 0.23.0`. Model configuration must reach the
server process before it starts. Create-time environment does not retroactively
configure a prewarmed port-9000 process. The SDK verifier below starts a new
port-9010 process with explicit configuration. Do not include credentials in
images or checked-in files.

```bash
abx kill <sandbox-id>
abx template delete <template-id> -y
```

## Quick start (Python SDK)

Install `agent-sandbox-client` using the [paired pinned source instructions](../docs/python-client-installation.md)
until the matching package is published. The import is `agent_sandbox`.

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox

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
for turns. The named server's HTTP files/process APIs return 404 under this policy;
the separate provider-native SDK management channel remains available.

### Independent native coding acceptance

From a checkout with the paired SDK installed, export `OPENAI_API_KEY` and
`OPENAI_BASE_URL` for an OpenAI-compatible, tool-capable endpoint. Set
`OPENAI_MODEL` to your actual model, for example `qwen3.8-flash`. Then run:

```bash
mkdir -m 700 /tmp/agents-cli-private-<unique-run>
python agents-cli/e2e_sdk.py --template <owned-agents-cli-template-id> \
  --journal /tmp/agents-cli-private-<unique-run>/journal.json \
  --report /tmp/agents-cli-private-<unique-run>/result.json
```

The controller calls `Sandbox.create(provider="alicloud-express")`, seeds a
disposable project through provider-native commands, and proves the exact initial
failure. It starts the unchanged installed commands and policy on port 9010 with
selected model configuration, its own server token, workspace and private state
directory. It retains the original `HOME`; host GitHub/cloud credentials are not
forwarded. It selects the exact native `--adapter` (default `qwen-code`, or `codex`), submits a genuine session/event, reconnects and polls items. Run each adapter with a fresh journal/report: `--adapter codex` exercises Codex independently; it cannot inherit a Qwen result. No synthetic CLI is selected. The new server explicitly selects the installed pinned Node24 PATH; no operator PATH is forwarded.

Independent native processes require changed existing source, byte-identical
original tests, exact JSON artifact values and a nonempty report, complete
original plus agent-written unittest modules, and six held-out cases. They compile
source under isolated Python and require a fresh post-agent random ACK, rejecting
skip, early exit0 and stale bytecode. A marker response cannot pass. The pinned
server's own private persisted turn state is additionally inspected for completed
status because this policy disables turn-status/SSE routes; this is an internal
diagnostic for server commit `e2cb27e`, not a new public API or artifact receipt.

The session API currently runs the agent with **full_access**. It does not accept
per-session permissions or time limits from the inline JSON. Closing HTTP
shell/files/process routes does not contain the CLI's tools or arbitrary same-user
code. Run only in a newly owned disposable sandbox without valuable files or
other credentials. The verifier checks ordinary correctness; it does not isolate
hostile code that can inspect or alter its own OS processes. The host turn deadline
defaults to 540 seconds (30–600 configurable); HTTP disconnect is not cancellation.
The owned sandbox TTL is 1800 seconds and the new server deadline is 1500 seconds;
these leave setup/evaluation headroom and do not replace immediate cleanup.
`finally` destroys the owned sandbox and checks a paginated provider listing for
its ID and random metadata nonce. A permission/readback failure fails acceptance
and retains the private recovery journal. Resolve its exact owned resources before
deleting the journal.

This controller does not deploy/delete a template or registry repository. The
owner who supplies the template handles those resources separately. Qwen success
does not establish Codex success: Codex 0.162.1 requires a compatible Responses
endpoint, and its coding branch needs independent acceptance.

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
may appear in items. The current session view can return idle without exposing
the final turn's error; accepting an event or observing idle does not prove model
success. The SDK verifier independently inspects results. An HTTP timeout does
not cancel an upstream turn.


For `--adapter codex`, the controller creates a fresh private CODEX_HOME with an explicit compatible HTTP Responses provider and websockets disabled. The key is referenced by OPENAI_API_KEY, never written into that config. This selects the approved endpoint deliberately instead of relying on ambient native provider defaults; the entire owned sandbox/profile is removed on cleanup.

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
