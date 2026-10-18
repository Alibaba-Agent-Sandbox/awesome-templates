# Decision: Require completed source-byte coding verifiers

Status: proposed

## Problem

Four standalone coding acceptance controllers can accept an incorrect calculator when its held-out import prints the static success marker and exits before assertions. Actual verifier subprocesses reproduce this at the frozen Pi parent a361f490555ead0ff67081ffb4874abf292a1b2f. Original three tests genuinely pass; untested held-out arithmetic remains incorrect. HTTP/model edits in this reproduction are fixtures, not real model proof.

## Decision

Keep each template standalone. Its controller runs isolated Python with trusted stdlib loaded before the project path, directly compiles actual source bytes, catches BaseException and accepts only a fresh completion ACK created after the model response. The original suite must contain and execute exactly three tests, with no failures/errors/skips/expected failures/unexpected successes. Preserve existing task, setup/key/disable guards, file/test/report/exact-marker checks and cleanup. Product runtime, image, model configuration and commands are unchanged. These checks are not an OS security boundary against arbitrary hostile Python.

## API Design

N/A — no product API changes. Existing opt-in controller environment remains unchanged.

## Alternatives considered

A fixed marker/exit code or stderr test summary admits premature exit. Importing source through normal importlib can consume agent-written stale pyc. A cross-directory shared helper would break standalone Docker contexts, so the small verifier is kept in each controller.

## Dependencies

Issue https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/98 . Original slices: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/41 , https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/26 , https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/27 , https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/28 . Codex equivalent: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/97 .

## Test Strategy

Run actual verifier subprocesses through both direct fixtures and complete HTTP/model-edit fixtures: correct source, exact static-marker/SystemExit counterexample, os._exit, wrong held-out source, proven stale unchecked-hash bytecode, cwd unittest/sitecustomize shadows, syntax errors, skipped/expected-failure/unexpected-success and wrong/empty suite counts. Keep existing process/privacy/HTTP behavior regressions. Run strict conformance/spec checks and existing local HTTP suites. Parent separately executes real model acceptance on unchanged reviewed image commands with pinned new host controllers.

## Acceptance criteria

No reproduced premature-exit/cached-source false pass; correct original three tests and held-out inputs succeed. Required existing checks and latest-head CI pass. Real-model evidence records exact new controller hashes/image provenance without changing historical reports. Canonical Express deploy/provider promotion remain pending and PR stays draft until mandated gates are complete.
