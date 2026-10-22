# Decision: Use current Express CLI in runnable template examples

Status: implemented

## Problem
Template READMEs and the skeleton used legacy --template/-y create and -y kill; side notes required readers to translate the main copyable block themselves.

## Decision
Use create TEMPLATE --detach and kill ID in active bilingual README/shared usage examples. Pin the shared setup to the reviewed current CLI source. Keep dated research, historical receipts and the documented old native acceptance harness unchanged; explicitly label that harness separately from current usage. No runtime/image/catalog acceptance changes.

## API Design
N/A — this decision does not involve API changes. Proposed diagnostics interfaces, when relevant, are explicitly unimplemented design, not current configuration or routes.

## Alternatives considered
- Keep the obsolete example and ask readers to translate it — repeats an avoidable installed-CLI failure.
- Edit generated website or Registry output directly — loses source ownership and will be overwritten.

## Dependencies
Current Express CLI contract and each repository's own source integration. https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/190

## Test Strategy
Document links, spec tools, strict all-template check, existing document checker tests and syntax validation against the built current CLI. No unrelated image/cloud/model workloads for prose.

## Acceptance criteria
All current template and skeleton examples use the current Express parser; translations and links pass; no new provider verification claims or modified historical receipts.

## Evidence
- [Verification](../../../evidence/verify/2026-10-22-current-express-cli-examples.md)

## Implementation
The scoped local implementation and validation are recorded above. Remote delivery is tracked by the owner PR; this status is not a claim that publication or merge already occurred. Outstanding gates remain explicit in the verification evidence.
