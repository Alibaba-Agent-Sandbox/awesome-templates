# Decision: Current Codex SDK image acceptance

Status: proposed

## Problem

[Issue16](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/16) requires the current pinned native Codex runtime, useful compatible-model behavior, actual SDK-created Express deployment and independently confirmed cleanup. Historical source-only/model and basic step results have separate scopes.

## Decision

Qualify unchanged2.0.0 using an exact-source CI image and actual Sandbox.create. Configure the owned native command server explicitly inside a fresh cloud sandbox. Require real model source edits/new artifacts, unchanged original tests and independent assertions. Run generated code only in the owned cloud sandbox and retain public provenance plus independent cleanup. Keep the native Responses configuration and documented explicit permission choices; no runtime contract is changed for acceptance.

## API Design

Existing named commands, typed arguments, configuration and CLI/SDK/HTTP usage remain. Actual SDK creation and native CLI/SDK smoke are distinct from the existing strict external HTTP model controller. Basic model-off skips cannot certify a real model run; the separate strict controller must succeed with zero failures/skips.

## Alternatives considered

Do not infer protocol failure without executing the pinned native client. A marker-only response, source-only model test, version/basic smoke or deletion acknowledgment cannot replace current image/source/code/artifact/assertion/cleanup acceptance. Never execute generated code on the operator host.

## Dependencies

Codex native package0.162.1 and sourceca3118e5123e7ce2ae2e43e2a8a05c88ecf3653d, explicit image artifact12267977528/export39430931693 and actual injected servere2cb27e24fde0a67112f82b8d44af463445a5d1a. Approved compatible endpoint credentials remain runtime-local. The native provider uses Responses. Standalone Docker fallback and actual injected source retain separate identities.

## Test Strategy

Check exact archive/source/non-root context, private registry visibility/digest before registration and after runtime, official READY, SDK create and native CLI/SDK commands. Strict model verification independently reads modified existing code and a new artifact, executes unchanged original tests and independent fresh assertions in the isolated cloud. Independently confirm sandbox/template/registry absence; retain old failures. Run targeted source regressions, strict template/docs and current-head mandatory CI.

## Acceptance criteria

Current-image native SDK/model and independent cloud cleanup pass; bilingual qualification and engineering evidence agree; required source/CI gates pass; normal scoped PR merges and remoteIssue16closure is confirmed.

## Evidence

[Verification](../../../evidence/verify/2026-10-20-codex-sdk-image-acceptance.md).
