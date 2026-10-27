# Express local push-tag cleanup verification

Date: 2026-10-27

Result: PARTIAL — focused regression and real patched cleanup pass; current-head CI pending.

## Inputs and scope

Changed files: `scripts/public_launch_e2e.py` and
`scripts/test_public_launch_e2e.py`, based on
`cf43f46a525e48236cc8189a8c8ee86c0b948d05`.
Linux amd64, Python 3.13, Docker 26.1.5; published CLI 0.5.7 and Python
client/server 0.4.0a6 were used by the observed source attempts.

This corrects verifier resource cleanup. It does not certify all templates,
model/vendor authentication, or another backend.

## Reproduction and regression

- Real serial source attempts retained their local registry-qualified image tag
  after the old verifier reported prepared artifacts absent. Their original
  reports remain unchanged; exact owned follow-up deletion/absence is separately
  recorded. No shared image/repository was deleted.
- `python -m unittest discover -s scripts -p test_public_launch_e2e.py`:
  before the implementation change, 35 tests ran and 3 regression tests failed.
  After the change, 35 tests passed. Cases include actual Docker refusal or
  still-present readback being retained as failure, already-absent reconciliation,
  and the existing alias/namespace ownership checks. These are controller unit
  tests, not independent live-cloud passes.
- `python scripts/check_docs.py`: PASS, 222 documents and zero local link failures.
- `python scripts/test_spec_tools.py`: PASS, 39 tests. Expected invalid-fixture
  diagnostics remain expected test output, not catalog failures.
- `git diff --check`: PASS.

## Live corrected cleanup

PASS: the patched function reconciled the original journal entry from the new
successful OpenCode Express source attempt. That source attempt used unchanged
public source cf43f46a525e48236cc8189a8c8ee86c0b948d05, public CLI 0.5.7 and SDK
0.4.0a6. The old verifier's full HTTP controller passed 16 checks; real-model
acceptance was not run and remains separate. The patched function independently
confirmed the owned remote ACR tag absent, removed the remaining 832 MB local
registry-qualified tag, and independently confirmed local absence. The source
attempt had already independently confirmed sandbox, registered-template and
local build-tag absence. No broad pruning was used by the fix.

## Remaining gates

Current-head CI remains pending. The broader per-template business/model matrix
is not certified by this cleanup repair.

Issue: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/238
