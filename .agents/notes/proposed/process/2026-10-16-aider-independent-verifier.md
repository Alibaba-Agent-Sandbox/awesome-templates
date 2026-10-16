# Aider independent verifier completion

Status: proposed

## Problem

An actual subprocess reproduction against `9bcc1a1` showed all coding checks
passing when the target only handled the original three inputs and printed a
static held-out marker before exiting zero. No held-out assertion executed.
Refs https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/50 and
https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/98.

## Decision

Keep the original read-only review, explicit selected-file writeback and genuine
coding task. Compile actual source in isolated trusted verifier processes, require
all three original tests successful without skips/expected failures, catch
BaseException and require separate fresh post-agent completion acknowledgements
for tests and held-out calculations. This is not an OS security boundary.

## API Design

No commands, runtime, template configuration or image-install contract changes.
The standalone HTTP controller uses the existing direct-exec shell API. Regression
fixtures follow its actual shlex.split plus shell=False semantics.

## Alternatives considered

A zero exit code or printed unittest count alone permits premature-exit false
positives. Retain genuine historical model results, but do not substitute them
for execution of this corrected verifier.

## Dependencies

Existing Aider product and image:
https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/88.
The same completion design is reviewed for four other controllers in
https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/100.

## Test Strategy

Run real subprocess positive and negative fixtures, strict template checks,
record/link checks and normal CI. Then execute the corrected controller against
the reviewed unchanged image with the authorized compatible model, verifying
owned sandbox/template/registry cleanup independently.

## Acceptance criteria

- [x] Actual direct-exec reproduction demonstrates the old false positive.
- [x] Correct source passes; early exit, skipped tests and stale cache fail.
- [x] Historical evidence remains unchanged; no provider promotion.
- [ ] Corrected controller actual-image/model acceptance and owned cleanup.
- [ ] Required parent, canonical deployment and final CI gates pass before merge.
