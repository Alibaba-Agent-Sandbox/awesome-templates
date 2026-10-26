# Decision: Maintain standalone template helpers from canonical sources

Status: proposed

## Problem

Repeated owned-process functions and the identical QM invocation adapter were maintained independently. A correction had to be repeated in many template directories.

## Decision

Retain standalone commands.py files while generating their repeated helpers from reviewed canonical function sources. Check all 15 helper placements in CI. Keep four process policies and the QM adapter distinct; do not force different input, output-limit, timeout-label or confirmation policies into one runtime API. The initial migration asserts identical executable ASTs before adding source markers.

## API Design

N/A — no runtime signature, dependency, model or template behavior changes. Run scripts/sync_process_runners.py to regenerate and --check to detect drift.

## Alternatives considered

- Import sibling folders: breaks downloaded standalone templates.
- Introduce a new SDK runtime package: unnecessary release and dependency work for a maintenance-only change.
- Keep hand-maintained copies: repeated fixes remain error-prone.

## Dependencies

Python standard library only for synchronization. Existing template tests/runtime dependencies remain unchanged. Related user journey: https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues/189.

## Test Strategy

Verify canonical copies, AST equivalence of the migration, relevant subprocess cleanup/stdin/timeout/output regressions, documentation and existing catalog checks. Distinguish unavailable pinned tool binaries from process-helper passes.

## Acceptance criteria

- All 15 placements have a reviewed canonical source and CI drift detection.
- Existing template signatures and AST behavior remain identical.
- Each template remains independent of sibling paths and unpublished packages.
- Verification records actual tool/version limitations without new cloud/model claims.

## Evidence

- [Verification](../../../evidence/verify/2026-10-26-runtime-helper-sources.md).
