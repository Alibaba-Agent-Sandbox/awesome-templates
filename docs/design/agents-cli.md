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

Template2.0.1 explicitly owns /home/user/app as user:user before runtime USER. This repairs actual non-root workspace mkdir/write failures. Earlier provider receipts retain their original source-version scope; this changed profile requires new acceptance.

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

## Independent Qwen SDK acceptance

`agents-cli/e2e_sdk.py` owns an Express sandbox from `Sandbox.create` through
`finally` kill and paginated ID/nonce absence verification. It accepts a private
pre-provisioned template ID; template/registry lifecycle belongs to the caller.
It compares installed commands/policy hashes, seeds an existing-source project
through provider-native SDK commands, and verifies the precise broken baseline
(`test_zero` PASS, `test_seven` FAIL). It starts original installed commands/policy on a
new9010 process with selected OPENAI key/base/model, a fresh server token and
private workspace/state directory, consuming the lazy process stream. Original
HOME is retained; no host/cloud/GitHub credentials enter target env. A create-time
env does not retroactively configure prewarmed9000.

One actual Qwen session submits a coding task and polls items/reconnect until
idle. The fixed server's idle state alone cannot prove the final turn succeeded:
wire_sessions maps terminal turn events to SSE, but this policy permits only
POST events, not GET events or turn-status routes. Native code therefore reads
the original e2cb27e server's own explicit private state directory and requires
this session's sole turn completed without error. This is internal diagnostic
observation, not a public endpoint, receipt, transcript export, or standalone
coding proof. The sanitized report stores only checks/statuses.

Independent isolated Python processes compile exact source bytes (not .pyc),
compare original tests byte-for-byte, require changed existing source, exact JSON
artifact and a nonempty report, run complete original and generated unittest
modules without skips/expected failures, and run six held-out cases. Each call
requires an unpredictable ACK generated after the agent finishes; exit0 without
that ACK fails. No arbitrary verifier command/hook or external receipt is trusted.
The HTTP-only e2e still rejects E2E_REQUIRE_LLM/E2E_RUN_LLM and points to this SDK
controller. No-network regressions prove false-green/cleanup guards, not a model
or provider run.

The inline session API maps to full_access by default and offers no per-session
permission/limit overrides. Model execution must use a newly owned disposable
sandbox without other credentials/valuable data. The host polling deadline is
30–600 seconds; disconnect does not cancel a background turn. Entire-sandbox
destruction is the resource boundary, including agent subprocesses that detach.
The sandbox/server deadlines are1800/1500 seconds to leave bounded setup and
evaluation headroom; neither replaces the immediate finally cleanup.
These are ordinary correctness controls, not isolation from arbitrary hostile
same-user code capable of inspecting or altering its own processes. Failed
cleanup/readback fails acceptance and retains an atomic mode0600 private recovery
journal. One permission error stops that path. Qwen compatibility uses existing
OpenAI-compatible auth; Codex Responses compatibility remains independently
unverified by this Qwen suite. Canonical deploy and formal provider metadata
remain unchanged until their actual separate gates pass.

Actual-image evidence on2026-10-16: the frozen host SDK controller1f975ff passed
real Qwen coding against original artifact12026073735/sourcea361f49, whose four
product runtime/build/config files are identical. All8 lifecycle flags and5
independent post-run absence checks passed. See [image SDK result](../../agents-cli/evidence/qwen-image-sdk-2026-10-16.json)
and [strict readback](../../agents-cli/evidence/qwen-image-sdk-strict-readback-2026-10-16.json).
Canonical deploy, Codex and formal metadata are still separate incomplete gates.
