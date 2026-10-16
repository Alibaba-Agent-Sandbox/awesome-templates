# Codex existing-source acceptance

Status: proposed

## Problem

The real-model controller asks Codex to create a new implementation and new tests.
It can pass without fixing existing source or preserving independent original tests,
which leaves the specification's existing-project acceptance unverified.
Refs https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/16.

## Decision

Seed an incorrect Fibonacci implementation and two original unittest cases in the
unique owned remote project. Require the specific one-failure baseline before any
model call. Ask the real CLI to fix the source, preserve original tests, write a
report and an exact acceptance artifact, add coverage and execute tests. Read
remote artifacts independently and rerun both original and generated tests plus
held-out Fibonacci assertions. Independent review reproduced early-exit false positives in the first implementation. Isolated trusted verifier processes now compile actual source bytes, reject incomplete/skipped/expected-failing tests, catch BaseException and require fresh completion acknowledgements chosen after the agent exits. Preserve permission and successful-tool-event gates.

## API Design

No runtime API or image change. The HTTP acceptance controller uses existing files
and direct-exec shell APIs; it does not use host paths for remote artifacts. Model
execution remains opt-in, with required-model mode failing on missing credentials.

## Alternatives considered

Counting a marker or generated tests alone cannot establish existing-source work.
An independent external image verifier supplies useful evidence, but must not be
substituted for maintaining the repository's repeatable acceptance controller.

## Dependencies

The unchanged pinned Codex image and reviewed parent:
https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/86.
Canonical deployment remains a separate gate:
https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/92.

## Test Strategy

Execute the real direct-exec semantics against local remote-server fixtures.
Reject changed original tests, unchanged source, missing report, and incorrect
held-out answers. Run the template checker and repository local HTTP suite. Record
actual image, cloud and model runs separately with exact controller provenance.

## Acceptance criteria

- [x] The specific existing-test failure precedes model execution.
- [x] Original tests, changed source, report and exact artifact are checked.
- [x] Independent hidden assertions and original/generated test reruns are required.
- [x] Positive and twelve invalid-baseline/artifact regressions exercise actual subprocesses.
- [ ] The updated public controller passes a real model run on a reviewed image.
- [ ] Required parent, canonical cloud and remote CI gates pass before normal merge.
