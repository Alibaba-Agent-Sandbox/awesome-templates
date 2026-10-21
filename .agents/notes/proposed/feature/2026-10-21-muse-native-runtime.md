# Decision: Original native Muse Code with an explicit compatible endpoint

Status: proposed

## Problem
[Issue71](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/71) requests actual Meta Muse Code. Earlier survey lacked an immutable installer; current official channel/release manifests now expose version1.4.11-R6667.1, Linuxx64 size384809176and upstream SHA256. A substitute same-named agent or install-only smoke would not meet the task.

## Decision
Install the exact original ELF under root-owned /opt/muse. Use original headless exec/miniswe/native tools and native completion/usage records. Explicit approved compatible Responses endpoint only. The original CLI requires /muse-code/models, absent on a general compatible gateway: provide one bounded local model-catalog/credential relay, forwarding Responses bytes unchanged to exactly the configured upstream. Native stdin receives a per-call random local token; the upstream key stays in the parent relay. No vendor/subscription fallback.

## API Design
Scalar muse(prompt,cwd,command_timeout), actual muse_version/native_check and read-only setup flags. Final reply and validated original native counts only, not raw thoughts/transcripts. One serialized operation; private per-call HOME/config, minimal tool environment, nonce/pidfd-owned process cleanup. Original settings schema_version1, endpoint_transport base_url/auth bearer and agents.execution_capacity1; miniswe has no available subagent_spawn.

## Alternatives considered
- Missing binary conclusion: superseded by actual official manifest and successful original native Express install.
- Direct compatible endpoint: actual original native startup fails404 on its required model catalogue; no model or coding assertion is reached.
- Generic replacement/tool loop or protocol translator: unnecessary; original Muse/Responses succeeds using a narrow model-catalog/credential relay.
- Forward operator keys to a vendor default: unauthorized and unnecessary.

## Dependencies
Original official Linuxx64 binary and published size/SHA from Meta release metadata. Original upstream terms/attribution remain separate from Apache-licensed template code. Python stdlib relay/process controls and pinned server source34e7e011c5569f77b7f605e65313be7498f6cf02 (SDK PR82 merged). No new third-party Python/Node dependencies.

## Test Strategy
Source-level path/deadline/privacy/relay redirect/headers/budgets and original native record correlation regressions; fixed-reply fixtures never execute generated code on operator. Actual non-root image, immutable source-bound canonical SDK-created Express steps/fullHTTP, original native synthetic routing before approved-key injection, then genuine native repair/artifacts/original+held-out tests with fresh post-return ACK and independently absent projects/native/listeners/cloud/OSS.

## Acceptance criteria
Full bilingual docs/design/catalog/spec, source/artifact license provenance, actual image/native SDK steps/HTTP and original model/tool/artifact acceptance pass, all prior failures and cleanup retained, current-head CI/review passes, and normal PR merge/readback before closing Issue71. Research-only coding/install success is not template qualification.

## Evidence
[Research](../../../evidence/verify/2026-10-21-muse-native-research.md).
