# OpenCode independent verifier completion

Status: proposed

## Problem

A real subprocess importing target calc.py could print the static expected marker
and exit zero before the legacy held-out assertions ran. Existing test-count text
also did not prove complete test execution.
Refs https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/98.

## Decision

Use isolated Python, preloaded trusted stdlib, direct source compilation and fresh
post-agent acknowledgements for original tests and both held-out phases. Require
all three original tests without skips/expected failures. Preserve exact-session
resume, original-file hashes, real artifact checks and historical model evidence.

## API Design

No runtime commands, Dockerfile, YAML, model settings or public API change.
The host-only HTTP controller still uses existing remote files/shell interfaces.
Completion verification is not hostile same-user-code isolation.

## Alternatives considered

Static stdout or zero exit alone permits incomplete execution. Reusing earlier
real-model evidence cannot verify the corrected gate.

## Dependencies

Parent https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/86.
Related completion guards https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/100.

## Test Strategy

Real subprocess protocol regressions with synthetic remote HTTP/model responses;
positive continuation, early exits, skipped originals, stale cache and stdlib
shadows; strict/doc checks, normal CI and genuine actual-image compatible-model
execution with exact owned cleanup.

## Acceptance criteria

- [x] Actual subprocess reproduction demonstrates the old gap.
- [x] Correct coding and continuation pass; incomplete execution is rejected.
- [x] Runtime/configuration and historical evidence remain unchanged.
- [ ] Hardened controller genuine actual-image/model run and cleanup.
- [ ] Parent, canonical deployment and normal final CI gates before merge.
