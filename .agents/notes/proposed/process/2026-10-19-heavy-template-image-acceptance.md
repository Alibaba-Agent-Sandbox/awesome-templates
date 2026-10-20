# Decision: Heavy template image acceptance records
Status: proposed

## Problem

Heavy step builds timed out while successful CI images alone did not establish runtime acceptance. Digest-form provider registration attempted latest and failed; failed records must remain.

## Decision

Record genuine exact-source CI image acceptance, using nonce-owned private registry tags with before/after content-digest readback. Keep failed step/digest attempts separate and add independently confirmed full resource cleanup. Provider badges identify exact image/model scope.

## API Design

No runtime command/dependency change. Only current tested_on/README metadata and distinct immutable receipt files. The orchestration implementation is separate PR129.

## Alternatives considered

Source-only/CI-only/network diagnostics cannot certify the product. Failed builds must not be relabeled. An unchanged runtime image may be reviewed using the original verified archive after source/config/command/archive revalidation.

## Dependencies

Issue119 and owner template Issues. Existing keyless CI image exports, genuine native SDK/CLI, provider official READY API, pinned server source and actual compatible model endpoint.

## Test Strategy

Current source hashes and real actual-image smoke, external HTTP, strict model verifier, independent sandbox/template/registry absence; docs/spec and current-head CI.

## Acceptance criteria

Scoped accurate provider metadata, preserved history, no credentials or private endpoints, current-head CI and ordinary reviewed merge. Full task and individual Issues remain open where other acceptance criteria are not delivered.
