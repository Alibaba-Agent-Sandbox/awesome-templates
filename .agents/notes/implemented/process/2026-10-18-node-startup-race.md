# Decision: reject nonexistent Node entries before startup
Status: implemented

## Problem

Current main sleeps one second, then treats a live Node process as successful
startup. Slow startup returns HTTP 200 for a nonexistent entry. PR111 has one
passing PR-event run and one failing push-event run on the same reported head.
Both installed SDK3c27c67568e7c53165ea60b32b109f208cca22ad. Their missing-entry
results differ; a passing retry is insufficient to establish correctness.

## Decision

Validate the entry is an existing file before spawning Node. Keep the current
HTTP500 contract and document that early process liveness is not HTTP readiness.
Keep PR and main checks, restrict push events to main to remove duplicate feature
runs, and pin the cross-repository SDK input to accepted main e43a4d8e.
Run the delayed-real-Node regression in the retained basic CI job. This does not
add cloud/model execution to Actions; the user's acceptance runs locally on Express.

## API Design

No command name, argument, response or valid-file launch change. Missing entry
files deterministically raise RuntimeError before process creation. The complete
readiness/lifecycle redesign remains independently reviewable in PR109.

## Alternatives considered

Ignore the failing push check: hides a real runtime bug. Increase sleep: still
has an arbitrary timing boundary. Remove PR checks: loses merge integration
coverage. Keep mutable SDK main: prevents reproducing the dependency input.

## Dependencies

Refs https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/112
and https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/29.
Related integration https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/109.
This fix does not establish acceptance of all 23 integrated templates.

## Test Strategy

Use a three-second launcher delay before the actual Node binary; the baseline
incorrectly succeeds after one second. Clean up the test's owned process group
and reap it in finally. Verify the real local Node HTTP suite and static tools.
Inspect exact-head required checks and review before merging.

## Acceptance criteria

- Delayed-start missing-entry regression fails before/pass after.
- Actual Node HTTP positive and error paths still pass.
- Preserve PR/main checks and failed historical runs; no provider badge added.
- Record cloud/image limitations separately from local checks.
