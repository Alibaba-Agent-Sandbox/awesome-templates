# Decision: Integrate every template into one exact-source acceptance branch
Status: proposed

## Problem

Twenty-three template products exist across separate feature heads. The
canonical review controller selected only17 and older inputs, so `all` could
not establish acceptance for the full catalog or its latest verifier fixes.

## Decision

Combine existing scoped PR sources with ordinary merges and preserve their
records. Retain both document/media native jobs and every specialized test.
Pin all23 combined Docker inputs and the cleanup-fixed harness to b30833c469e0e6b4fa5ee2134391b276dbb42c8e.
Expand the strict controller whitelist with Aider, SWE, OSWorld, OCR, media and
document tools; regression-check equality with the catalog. Keep cloud default
disabled, exact-head authorization, private journals and owned cleanup gates.

## API Design

No template command/runtime/version or provider badge changes. CLI, SDK and
HTTP POST documentation is retained per template, with shared installation,
authentication and ownership guidance. `all` now selects23 reviewed inputs.

## Alternatives considered

- Accept unrelated green image jobs as canonical provider proof: false claim.
- Rebuild only the original17: omits six implemented products and new verifiers.
- Upload cloud configuration without explicit storage approval: unauthorized.

## Dependencies

All scoped template PRs82/86/91/92/94/96/97/99/100/101/102/103/104/105/106/107/108
remain independently reviewable on
https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pulls.
Production CLI wheel integration remains
https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/pull/37.
Controller SDK auth contract landed in
https://github.com/Alibaba-Agent-Sandbox/python-sdk/pull/56.
Server wheel source remains independently pinned. Registry/website ingest source
docs/catalog; no default-branch publication or provider support claim is made.

## Test Strategy

Strict spec/checker, all local regression groups, real source HTTP where
available, all23 exact-head hosted image jobs and specialized native jobs.
Canonical deploy/provider proof remains blocked until explicit temporary
Actions-secret storage approval. L3/model and full external HTTP remain separate.

## Acceptance criteria

- Exactly23 unique products; no dropped catalog entry/native job/test group.
- Strict checker and controller selection/gates pass.
- Every template has bilingual CLI/SDK/POST guidance and honest provider state.
- Latest-head CI passes; real cloud receipts only follow actual deploy/cleanup.

## Evidence

[Verification](../../../evidence/verify/2026-10-18-integrated-template-acceptance.md).
