# agents-cli

## Purpose

Offer callers one restricted local Agents HTTP session surface over pinned Codex
and Qwen Code. Replace the previous runtime placeholder and automatic synthetic
CLI substitution with actual installations and truthful diagnostics. Refs
[Issue #25](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/25).

## Capabilities

Serve session creation/list/reconnect, queued messages, polled items and runtime
discovery on port 9000. A named version check runs both installed CLIs. Generic
shell, files, process APIs and the remaining Agents endpoints are disabled.
Upstream agent tools retain their configured subprocess permissions. This is a
local process/session implementation, not a hosted OpenAI service. Sessions do
not survive server restart.

## Exposed API

`agents_version() -> str` runs `codex --version` then `qwen --version`, each with a
20-second deadline, and requires exact pins. Success returns
`codex 0.162.1; qwen-code 0.23.0`; missing/wrong/error versions raise a sanitized
RuntimeError. No model call occurs.

The explicit policy opens list_commands, run_command and six runtime/session
endpoint IDs. Session creation accepts `adapter` (`codex` or `qwen-code`), an
agent model, and a self_hosted existing workspace path. Event submission returns
202; callers poll items and inspect results. Unsupported runtimes/routes are
404. Both direct Python startup and canonical start_cmd must load the same file;
canonical start_cmd passes `--policy` explicitly so import-time command
registration cannot silently leave the default shell/files surface open.

## How to build

[Dockerfile](../../agents-cli/Dockerfile) retains the Alibaba base, generation 2,
non-root user and no CMD/ENTRYPOINT. Installs pin `@openai/codex@0.162.1`,
`@qwen-code/qwen-code@0.23.0`, and python-sdk server archive commit
`e2cb27e24fde0a67112f82b8d44af463445a5d1a` unless a source wheel is supplied.
The base Node 20 is below Qwen Code 0.23.0's declared Node>=22 requirement. Install official Node 24.16.0 from architecture-specific SHA256-verified archives using the same pinned installer as OpenClaw. Build logs must assert both actual CLI versions. commands.py and server-policy.json
are copied after package installation. Synthetic e2e-bin programs are not copied.

start_cmd is `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py --policy /home/user/app/server-policy.json`.
ready_cmd is `agent-sandbox-server healthcheck --port 9000`.
Resources: 2 vCPU and 4096 MB RAM.

## Express feasibility

Feasible: slice

Limiting factor: local session/runtime subset

The selected local HTTP API and CLI subprocesses require no Docker, KVM or
privileges inside the sandbox and can run as user. The full hosted Agents service
and other endpoint families are outside this slice. Image size, deployment and
model workload consumption remain unverified for the current source.

## Risks

Runtime keys must be injected, never baked into images, policy or logs. Server
ABX_SERVER_TOKEN and provider gateway authentication are separate. Closing HTTP
files/shell APIs is not a filesystem boundary around the upstream coding agent.
The policy must remain explicit for both startup forms; changing it changes the
contract. Version diagnostics never expose raw child output. Sessions cannot be
deleted/cancelled through this intentionally small allowlist. E2E_RUN_LLM=0 must
never activate synthetic production binaries.

## Test plan

L0: checker plus actual SDK server/real pinned CLI diagnostic and HTTP contracts;
create/read/list sessions without model turns, prove disabled endpoints remain
404. Separate pytest protocol fixtures explicitly inject e2e-bin into only their
own subprocess PATH and check both startup forms, wrong/missing token 401,
allowlist enforcement and two turns for each adapter. An empty test PATH proves
the model-disabled flag cannot enable fixtures automatically.

L1: actual image build with both version assertions and non-root runtime.
L2: deploy current image, create a sandbox and invoke agents_version through CLI
and SDK smoke; only after that may provider evidence be added.
L3: not implemented by this restricted HTTP smoke. Requires a genuine model turn
that modifies existing source, creates an artifact, and passes independently
executed tests observed through a separate authorized process/files channel.
ABX_E2E_OK response text or a fixture turn cannot establish acceptance. Requesting
required model acceptance in this smoke exits nonzero. L4 only after an actual
additional-provider run; none is claimed.
