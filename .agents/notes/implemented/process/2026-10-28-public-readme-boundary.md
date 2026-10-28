# Decision: Keep public template documentation focused on use

Status: implemented

## Problem

The repository README accumulated internal acceptance matrices, historical pass/fail counts,
repair checkpoints, controller descriptions and compatibility implementation notes. These
obscure template discovery and configuration and are outside the audience requested by the user.

## Decision

Remove those narratives, historical receipt columns and internal testing instructions from the
root README. Keep all 46 source-template links, descriptions and maintenance statuses and all four
managed-runtime links and provider identities. Explain launch and application-token setup in
English and Chinese. Extend both documentation standards to cover the root README and user guides.
Keep original engineering evidence unchanged in its established location.

## API Design

N/A — this decision does not involve API changes.

## Alternatives considered

- Remove only the reported paragraph: rejected because adjacent historical batches and internal
  implementation notes have the same audience problem.
- Delete original acceptance evidence: rejected because historical engineering records remain useful.

## Dependencies

No runtime or catalog dependency changes. Related CLI guidance is owned by
https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues/189.

## Test Strategy

Check every local Markdown target, compare source-template rows and managed identities with the
base revision, review both language instructions, and run diff and record-link checks. No cloud
execution is required for this prose-only change.

## Acceptance criteria

- Root README explains discovery, credentials, launch and documentation navigation.
- Internal matrices, pass/fail totals, repair checkpoints and historical receipt links are absent.
- Source-template entries/statuses and managed identities remain intact.
- English/Chinese standards express the same audience boundary.
- Scoped links and record checks pass; original historical evidence is unchanged.

## Evidence

- [Verification](../../../evidence/verify/2026-10-28-public-readme-boundary.md)
