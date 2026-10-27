# Decision: Native OpenClaw text conversations

Status: proposed

## Problem
Template2.1.3 provides gateway lifecycle but no callable model business workflow.

## Decision
Add explicit all-or-none compatible-model key/base/model startup settings and
`gateway_chat`, internally using the owned pinned native gateway. Preserve lifecycle
without model settings, independent gateway token and exact owned process cleanup.
Disable tools/channels/browser UI; keep native conversation state disposable.

## API Design
Template2.2.0 adds one named method, bounded UTF-8 prompt, session ID and wait.
Stable native `user` preserves per-thread context. No legacy vendor-key fallback.
Responses contain only session ID/text; upstream errors are sanitized. Stop deletes
private state. Client timeout is not native turn cancellation. Both README languages
provide CLI/full SDK/HTTP business use, model changes and extension boundaries.

## Alternatives considered
Gateway health cannot establish business use; direct calls to an external model
would bypass OpenClaw. Full messaging/channel product onboarding is separate scope.

## Dependencies
Issue https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/269; broader
https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/244 remains open.
Pinned OpenClaw2026.10.4/Node24.16.0, published server0.4.0a6 unchanged.

## Test Strategy
Focused input/config/session/error/ownership regressions; specification and docs
checks; actual source launch with all five methods, independent expense total and
same-session follow-up; literal CLI/full SDK/HTTP, second model, independent cleanup.

## Acceptance criteria
Actual pinned runtime accepts config and business tasks, complete receipts and
practical article, current-head CI/review, merge and public readback. Pending real
execution does not qualify this template or remove Beta.
