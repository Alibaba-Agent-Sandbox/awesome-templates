# Decision: Bind step receipts to the complete source manifest contract

Status: proposed

## Problem

During [PR152](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/152) review, the current-source classifier skipped template.yaml entirely except version/smoke. A synthetic unchanged-version receipt still passed after changing launch commands, resource limits and environment. This is a reproduced audit defect, not a new cloud run. [Review comment](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/152#issuecomment-6295663190), [tracking Issue149](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/149).

## Decision

New preparation provenance records a canonical SHA256 of the entire original source manifest excluding only tested_on qualification metadata. The read-only runtime/full-HTTP auditors require that contract and a valid raw manifest hash. An unchanged legacy raw manifest remains valid. If legacy bytes differ, recover the exact recorded bytes from local immutable Git history and verify their full recorded SHA256 before comparing normalized contracts. An explicitly recorded copy_source_commit must match its own file; legacy inline-copy receipts lacking a revision may search at most64local revisions of the one manifest path with bounded subprocess/time limits. Missing history remains MISSING. No receipt is rewritten and no cloud operation is added.

## API Design

Add source_manifest_contract_sha256 to steps provenance. Changes to start_cmd, ready_cmd, resources, env, ports, base, smoke or other manifest fields invalidate acceptance even at the same version. Only tested_on is excluded. An explicit current server-sdk.commit also requires its exact hashed input plus the effective selected SDK revision matching the validated current pin/Docker fallback. Existing audit CLI/JSON fields and step recipe bytes stay compatible; the stricter classifier rejects formerly misattributed PASS. Full HTTP acceptance inherits the same binding.

## Alternatives considered

Version equality and recorded Docker/commands alone miss runtime launch configuration. Ignoring all manifest bytes to preserve qualification updates is incorrect. Editing old receipts would destroy immutable evidence. Guessing the old YAML layout, making network fetches during audit or trusting a different recorded source revision is unnecessary. Exact raw SHA256 matching a local immutable historical blob establishes the old bytes; a shallow checkout without them cannot qualify.

## Dependencies

Existing PyYAML/stdlb/Git and source SDK-pin authority. Stacked on the reviewed PR152 source83a88853c82c0f4067fd9deed799e58dbd1125a8; no native dependency, provider policy, image/runtime/model contract or cloud credential change.

## Test Strategy

Regressions reject same-version launch/readiness/resources/env/ports/base/capability changes, missing/bad manifest hashes, wrong/missing source history and mismatched required SDK pins. Positive controls preserve only qualification changes, exact old manifests without Git, and qualification-only legacy history with/without a recorded immutable source. Existing materializer and full-HTTP/cleanup suites remain required. Read-only current-catalog audit reuses immutable existing cloud receipts, without claiming fresh execution.

## Acceptance criteria

Targeted and existing source/record/doc/CI checks pass. The reproduced changed-contract false PASS rejects; qualification-only history is honestly bound. Current33profile runtime/full-HTTP audit remains valid using exact existing receipts, with no rewritten evidence or invented cloud test. Latest-head review/checks and normal merge must land before the PR152 review gate is resolved.

[Verification](../../../evidence/verify/2026-10-20-step-manifest-receipt-binding.md).
