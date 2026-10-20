# Decision: pinned native local browser-use agent

Status: proposed

## Problem

[Issue51](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/51) needs a real browser agent rather than only Playwright primitives. Actual0.13.11 PyPI/source API is inspected; the survey's assumed Playwright dependency is obsolete for this package, which uses CDP-use.

## Decision

Exact hash-locked browser-use0.13.11, explicit Chromium1208 installed by pinned Playwright1.58 without duplicate shell, fresh native worker/private browser each call, explicit compatible text-DOM model. Disable cloud browser/telemetry/extensions and local file/shell/evaluate actions, no delegation. One browser operation per server.

## API Design

Read-only version/setup, actual model-free CDP self-test and typed browser_use(task,url,max_steps,command_timeout) structured result/final URL/new PNG/steps/done/success and bounded redacted native error summaries. Private file stdin for model settings, filtered child environment, bounded process identity/group cleanup. Complete bilingual command limits/errors/owned cleanup. SDK model verifier borrows supplied fresh sandbox and independently validates browser effects and cleanup; it never destroys a caller sandbox.

## Alternatives considered

A done string, mocked click or generated PNG cannot prove model browser work. Cloud Browser Use is not this local profile. Native cached target title did not update in the first self-test; actual actor get_title directly queries the target and fixed the test. Initial authored click fixture needed the actual multiline DOM index form, then native click independently changed the counter. No model-generated code runs on the operator host.

## Dependencies

Pinned browser-use0.13.11 MIT wheel SHA25650b0d16efc44215f99ed1c9197f05e2519bb79fa1501eed7371aff450cc56045, complete transitive lock generated with uv0.11.28/Python3.13, Chromium145/Playwright1.58 installer, fixed server/client SDK. Hash-lock strict checker support from [PR146](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/146) must land before this consumer. Preserve upstream and transitive notices.

## Test Strategy

Actual installed native library/Chromium, model-free navigation/title/PNG and authored model-response click/independent JS visit/counter/new PNG.5 native cases and7 acceptance guard cases passed before final lock/loopback/surface refinements; focused final rerun required. Negative static-done/unchanged counter/code/fake PNG/unrelated URL/failed native/boolean-byte cases must reject. Source/image/latest-head CI and actual SDK-created Express/native/real model/owned cleanup gates still pending.

## Acceptance criteria

Strict source/docs/image gates; actual SDK-created Express native CLI/SDK/full HTTP and real model browser counter3/submitted nonce/independent PNG; owned fixture/server/files/listeners and sandbox/template/registry cleanup; exact-version immutable evidence and clear step feasibility; normal merged PR before Issue51 closure. No earlier local fixture is promoted to provider/model acceptance.
