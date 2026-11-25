# Decision: Complete template author guidance and the existing Agents architecture map

Status: implemented

## Problem

The requested development convention, evaluation procedure and Agents API cloud
architecture were prepared in PRs300/301 but never merged. Their old branches
conflict with current documentation; historical CI failed before template tests
because a fixed external LibreOffice package was unavailable. Current source
also exposes internal build-file handoffs in the Agents README.

## Decision

Carry forward the bilingual convention, evaluation procedure and existing managed
architecture on current main. Correct obsolete CLI examples without changing the
Server SDK decorator or HTTP contract. Explain that the authenticated internal
bridge is not a claim of VPC-only networking. Remove manual build/receipt-file
handoffs from the affected application instructions; retain explicit ownership
of external databases, networks and images.

Preserve the original November9 assessment and November10 architecture evidence
byte-for-byte as dated source records. The 51-row assessment describes its frozen
source revision, not current catalog qualification or newly measured performance.
Do not relabel it as a fresh full-catalog AI review. Existing runtime manifests,
image pins, catalog identities and qualification remain unchanged.

## API Design

N/A — contributor guidance and resource explanation only. OpenAPI-bound business
operations use the already supported target-first CLI. Installation selects the independently verified CLI0.6.0-alpha.2 preview.
SDK0.4.0a7 image pins remain unchanged.

## Alternatives considered

Keeping useful documentation permanently unmerged because an old dependency
installation failed would leave the user's request unresolved. Blindly merging
old branches would restore retired command names. Inventing fresh scores, cloud
results or a universal quality rank would misrepresent the evidence. A new
runtime field, package release or cloud deployment is unnecessary.

## Dependencies

- [Original convention and assessment PR300](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/300)
- [Original cloud architecture PR301](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/301)
- [Current optional OpenAPI contract PR318](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/318)
- [CLI public workflow corrections PR277](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/pull/277)

## Test Strategy

Run current documentation, specification-tool and all-template checks. Verify
all historical file hashes and source trees against their exact Git revision.
Parse the SVG for unexpected executable/external content and inspect a rendered
image. Independently review both languages, current CLI requirements, resource
ownership and the distinction between static scores and execution evidence.

## Acceptance criteria

Current contributor navigation reaches both guides. Agents readers see the
Gateway/Dispatcher/Worker, Session Sandbox, database/model/image dependencies and
which resources they supply. No obsolete build-file handoff remains in the
changed application README. Exact-head CI passes and the replacement PR merges;
only then close the superseded original PRs with their replacement evidence.

## Evidence

[Verification](../../../evidence/verify/2026-11-25-template-guidance-completion.md).
