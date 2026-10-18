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
The user now requires locally initiated real Express deployment/model acceptance;
Actions cloud/model execution is not a task gate. No Actions secret upload is
needed for this local path. Image deploy remains blocked by the absent local
Docker Engine; source-runtime model runs are recorded separately. Preserve
basic PR/main checks, immutable inputs, exact ownership and cleanup readback.

## Acceptance criteria

- Exactly23 unique products; no dropped catalog entry/native job/test group.
- Strict checker and controller selection/gates pass.
- Every template has bilingual CLI/SDK/POST guidance and honest provider state.
- Latest-head CI passes; real cloud receipts only follow actual deploy/cleanup.

## Evidence

[Verification](../../../evidence/verify/2026-10-18-integrated-template-acceptance.md).

Final review also fixes Issue110: local cleanup previously deleted the active
agents-cli/e2e_sdk.py source. Restore that source and preserve Python verifier
files while still removing generated outputs; a real temporary-directory
regression fails before/pass after the fix. CI executes that regression. Use
accepted native SDK e86cb0b for controller/source-install examples, retaining
independent injected-server/harness pins. Restrict duplicate push jobs to main
while retaining every PR and main gate; no canonical acceptance is weakened.
https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/110

The current convergence ordinarily merges accepted main e258fdc2, preserving
both completed orphan retirement and the full integrated Node lifecycle. The
new delayed-Node regression also applies to the integrated ValueError API and
sets its own WORKSPACE explicitly. Retain specialized media/document jobs and
independently pinned server input e2cb27e; do not restore mutable SDK main.
