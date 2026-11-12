# Decision: Observe asynchronous preview logs within a bounded test deadline

Status: proposed

## Problem

The actual latest local-e2e run passes the Next HMR allowed-origin and rejected-origin network
assertions but fails its immediate buffered-log assertion. dev_logs explicitly returns a
snapshot, while a separate reader thread drains the child pipe. Websocket completion supplies
no synchronization barrier with that collector. The specific scheduler ordering in the CI
failure is not independently captured; it must not be presented as proven.

## Decision

Change only the existing HMR regression to poll its log snapshot for at most5 seconds using
monotonic time and short sleeps. Return from polling as soon as both original substrings are
present. Keep the final original warning AND exact rejected-host assertion, and preserve the
single real allowed-origin TEXT and denied-origin non-TEXT/HTTP-error websocket attempts.
No runtime flush API, package update, retrying websocket or weaker assertion is introduced.

## Alternatives considered

Remove the diagnostic assertion or accept only one substring: drops existing verification.
Fixed5-second sleep: delays successes without a condition. Retry network operations: changes
what is being tested. Add a runtime flush barrier: expands an established buffered API for a
test observer. Retry CI without correcting the observation assumption: leaves the race.

## Dependencies

Actual failure: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/43293813726/job/131446657105
atdfb9e413c0797b4279456426839272e145198200. Native toolchain stays at exact lockfile versions
Next16.4.2/React19.3.1/Vite8.3.4. Tracker:
https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/309.

## Test Strategy

Preserve the actual17-pass/1-fail CI identity and log hash. Copy the complete Next template
context to scratch, install its exact lock without executing package scripts, and run the
same two actual Next/Vite/controller test files (18 cases). Check package/test byte identity,
actual installed versions, dependency consistency, scoped lint, document links and whitespace.
Do not add artificial delayed-reader probes or another image/model/cloud matrix.

## Risks and Limitations

The diagnostic assertion still fails when the warning or exact hostname never arrives within
its deadline. This change fixes an invalid immediate-observation assumption; it does not prove
the precise original CI thread schedule. Local native-toolchain tests are not final remote CI
or cloud acceptance. Other local-e2e groups occur later and remain subject to the unchanged gate.

## Rollback Plan

Revert the test-only observation change while retaining the actual failure and verification
records. Do not weaken websocket origin restrictions or change runtime log contracts.
