# Decision: Diagnose actual OSWorld worker termination

Status: proposed

## Problem
Fresh public Express use intermittently reports worker EOF during the native smoke.
A prior full native controller passed but the expense workflow did not complete.
The cause is unverified; neither memory pressure nor native signal is yet established.

## Decision
Expose only numeric waitid exit/signal status at unexpected EOF, preserving the
unreaped leader identity and bounded exact owned cleanup. Collect private memory
events during the next actual attempt; never reflect task content/raw stderr.

## API Design
No command/schema change. Error detail may include safe numeric code/status.
No acceptance or Beta change from diagnostics alone.

## Alternatives considered
Blind retries, guessed RAM increases and weakening real GUI/evaluator gates cannot
establish the defect cause or complete the user's business workflow.

## Dependencies
Refs https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/244.
Pinned upstream/browser/Python dependencies unchanged.

## Test Strategy
Real child exits7 with EOF; require numeric exit information and exact owned cleanup.
Run ownership/task regressions and actual public-source desktop/core/expense flow.

## Acceptance criteria
Identify actual termination cause, repair any template issue, prove all methods
and literal consumers plus actual desktop results before qualification. Pending.
