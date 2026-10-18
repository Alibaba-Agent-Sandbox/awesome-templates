# Image CI checkpoint without provider promotion

Date: 2026-10-16
Status: proposed

## Problem

The current verification page still describes the first 13-success/3-failure
image matrix as awaiting a corrected run. Later actual runs have succeeded, and
Pi adds a seventeenth product. Keeping that stale status also obscures which
cloud/model and original-business requirements remain unaccepted.

## Decision

Update only the bilingual verification summary and owner records on an isolated
branch based on `a361f490555ead0ff67081ffb4874abf292a1b2f`. Preserve the first
failure evidence. Add public GitHub run/job snapshots for the corrected 16-image
matrix and the later 17-image matrix. Keep all current provider/catalog statuses
unchanged. This is a draft checkpoint, not authorization to merge its parent.

## API Design

No runtime API, template, catalog or workflow changes. Distinguish actual L1,
source-runtime model checks and supplementary changed-image cloud verification.
The existing canonical L2 gate remains unchanged: deployment via `abx template
deploy` and an exit-zero `scripts/express_e2e.py` before canonical provider-pass
evidence or `tested_on`/Verified updates.

## Alternatives considered

- Overwrite the failed run: rejected because it would erase useful provenance.
- Call any official registration plus smoke L2: rejected because the contributor
  rules explicitly require the canonical deploy/runner path.
- Include pending Aider/OSWorld/cloud work: rejected because an in-progress slice
  and a running attempt do not establish acceptance.

## Dependencies

[Pi PR 86](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/86)
is the stacked base. Existing per-template and first-image evidence remains
authoritative for its recorded revision. No credentials or raw logs are added.

## Test Strategy

Read actual GitHub workflow/job state, check public links and relative document
targets, run the strict static checker and inspect the scoped diff. This prose
change does not justify rerunning cloud/model workloads locally. Remote checks
remain pending until they actually execute on the draft head.

## Acceptance criteria

- Both actual successful image matrices are recorded with exact hashes/URLs.
- First failures, the separate production-image HTTP-suite failure and cleanup
  remain visible; pending reruns are not converted into passes.
- Seventeen products plus skeleton, Pi's local-only model scope and unfinished
  Aider/OSWorld/original roadmap are stated accurately in English and Chinese.
- No canonical provider-pass file, catalog promotion or gate relaxation occurs.
- Scoped document/static checks pass; PR stays draft and unmerged as requested.
