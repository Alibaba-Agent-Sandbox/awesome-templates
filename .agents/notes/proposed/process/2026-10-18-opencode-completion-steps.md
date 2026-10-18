# Decision: verify completed OpenCode final steps
Status: proposed

## Problem

Real Express runs returned HTTP200, tool steps, multiple text events and a
session, but L3 compared the documented all-step aggregate text with a final
marker. Intermediate commentary falsely rejects completion before independent
artifact and exact-session checks run. Failed attempts remain failed evidence.

## Decision

Keep the command API unchanged. Parse the sanitized JSON stdout in the verifier;
require the final completed stop step, same session and exact marker. Reject
unfinished/tool-only/error/malformed streams. Keep every existing independent
source/test/artifact/held-out/resume assertion. This fixes the acceptance parser,
not model output or public command behavior.

## API Design

No new command/result fields or runtime capability changes. `text` still joins
all text events; `stdout` retains sanitized step boundaries. Bilingual docs
explain how strict final-response verification uses that existing stream.

## Alternatives considered

Ignore all extra text or accept a marker anywhere: permits false completion.
Change aggregate text API to final-only: unnecessary compatibility break.
Disable real model tests: violates the user's local Express acceptance request.

## Dependencies

Refs https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/114
and https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/109.
Upstream pinned event emitter:
https://github.com/anomalyco/opencode/blob/v1.19.0/packages/opencode/src/cli/cmd/run.ts
and step-finish schema:
https://github.com/anomalyco/opencode/blob/v1.19.0/packages/opencode/src/session/message-v2.ts.

## Test Strategy

Existing remote coding protocol with real independent local Python subprocesses,
now with/without intermediate commentary. Preserve tampered-test/artifact,
premature-exit, stale-bytecode and wrong-session negatives. Add truncated,
tool-only, wrong-session, error, unfinished-next-step and malformed JSON rejects.
Re-run strict real coding and exact-session resume locally against Express.

## Acceptance criteria

- Valid multi-step regression FAIL before/PASS after.
- All false-success negatives remain effective.
- Real model and independent cleanup outcomes recorded separately from fixtures.
- No provider badge, Dockerfile/runtime or Actions secret changes.
