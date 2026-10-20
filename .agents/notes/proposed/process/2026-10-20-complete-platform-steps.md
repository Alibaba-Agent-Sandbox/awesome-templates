# Decision: Complete current-catalog platform-step acceptance

Status: proposed

## Problem

Current main has current-version steps acceptance for only part of its source catalog. Image/model receipts and historical versions do not certify the missing step profiles. Real official-asset downloads also exceeded existing installer deadlines.

## Decision

Use an optional temporary private same-account OSS cache when direct official downloads cannot finish within the provider build stream. Only exact official archives enter the cache; private ACL/object metadata are independently read back. The private execution recipe contains short-lived GET authorization for these public artifacts, never an operator access secret or model setting. Private recipes stay outside Git/Actions in0700 staging. Sandbox/template and exact owned objects/bucket must all be independently absent before publication. Track the remaining profiles in https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/149, linked to https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/119. Add a read-only acceptance audit requiring exact current versions, unchanged build/runtime input hashes, successful current CLI/SDK smoke calls and independent cleanup. Extend the canonical step runner with an optional unchanged external HTTP controller. Keep model outcomes distinct. Add an explicit parallel asset-transport option for reviewed archive installers and hash-locked Python graphs, retaining original source bytes, official SHA256/version checks and non-root runtime.

## API Design

`scripts/step_acceptance.py --require-http` exits nonzero while any current catalog profile lacks its matching runtime/CLI/SDK or unchanged full external HTTP controller receipt. Default mode preserves the narrower smoke audit. `run_steps_e2e.py --http` executes external functional controls in canonical ownership; skipped model cases remain NOT_RUN. `--asset-transport parallel` prefetches exact public archives using verified bounded ranges into a temporary build-only cache; a process-local Python adapter lets the original installer consume those same bytes. Original direct transport remains the default.

## Alternatives considered

Reclassifying image-only success or older versions would invent coverage. Removing byte/deadline/hash/cleanup controls would hide defects. Copying operator credentials into Actions is unnecessary. A general Dockerfile interpreter remains out of scope.

## Dependencies

Existing authorized Express API, reviewed native CLI and paired Python SDK/server. The CLI ENV argument correction is owned by https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues/84 and must land independently. No provider policy or shared account configuration is changed.

The full functional closure also includes [OpenCode ownership Issue156](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/156): template2.0.2 fixes the post-install non-root state handoff and read-only setup diagnostics; prior image/model versions remain historical.

## Test Strategy

Reject historical/image/provider/changed-source/SDK-only/uncertain-cleanup receipts. Execute actual HTTP controller subprocess positive and negative controls with credential isolation. Reconstruct exact ranged HTTP bytes and reject incorrect range/size/digest/cache data. Run all existing materializer/ownership/source/docs gates. Execute genuine current-version cloud step recipes and independent owned cleanup, retaining failed attempts immutably.

## Acceptance criteria

- Every current catalog source profile has its own matching real step READY/CLI/SDK/cleanup receipt.
- Applicable full external functionality is executed, with model/image scopes stated separately.
- Build transport retains official bytes, hashes and versions; no temporary cache remains in runtime.
- Bilingual operations, an auditable catalog matrix and immutable evidence are published.
- All mandatory latest-head CI/reviews pass and normal PR merge is independently confirmed.
