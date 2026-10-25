# Decision: Preserve public Express rerun provenance and managed entry points

Status: proposed

## Problem

The developer rerun starts with published tools and the current public catalog. Existing managed acceptance still uses obsolete CLI syntax and retired workflow labels. The image consumer needs to distinguish the exact public template input from a verifier-only workflow revision, and source-built historical images from a new published-tool launch export.

## Decision

Use the existing managed verifier with current bare-name CLI launch and ProviderSandbox, actual numerical processing and exact known-ID cleanup even when SDK connect or CLI kill fails. Accept only explicitly labelled public image exports with official package provenance, observed runtime server version, immutable public source input and a separate verifier revision. Retain historical L1 scope and leave ambiguous resources unresolved. A prepared-image Express run remains separate from a default source launch.

## API Design

No product API/schema changes. The acceptance scripts preserve separate immutable receipts and consumer origins. Prepared-image registration leaves application startup to the existing unified `template launch`: a private manifest adds the exact owned template ID/provider and retains original services, startup and environment. There is no second service, SDK creation selector, workflow selector or platform fallback.

## Alternatives considered

Reusing historical success as a new rerun, rewriting old receipts, or replacing another provider's managed identity would be inaccurate. A missing Docker host cannot be called a source-build pass. Reusing a byte-verified image avoids duplicate builds while stating the narrower prepared-image scope. The one-time reconciliation of incorrectly labelled old exports stays only in the frozen experiment artifact; maintained tooling rejects those old records and does not guess or migrate a source revision.

## Dependencies

Published CLI/Python packages, the current public catalog, reviewed public launch export workflow, existing ACR/crane transfer and ownership cleanup tooling. CLI defects have separate owner Issues and PRs.

## Test Strategy

Fresh official website binary and npm/PyPI installations; actual Express managed lifecycle and dataframe assertions; failure-path cleanup regressions; public export revision/provenance regressions; all source images and unchanged HTTP controllers after suitable real exports are available. Preserve failures/skips and independently verify exact owned cleanup.

## Acceptance criteria

No missing-package, cross-provider mismatch, missing Docker or failed workflow is counted as a runtime pass. Current managed CLI entry points and all successful real consumer calls are reproducible. All source template/provider results remain incomplete until individually observed and cleanup is confirmed.

## Evidence

- [Verification](../../../evidence/verify/2026-10-25-public-express-rerun.md)
- Related provider/source journey: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/215
- Binary defect: https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues/156
- Docker preflight defect: https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues/160
