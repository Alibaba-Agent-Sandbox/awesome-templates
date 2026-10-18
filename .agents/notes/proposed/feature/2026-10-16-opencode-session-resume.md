# Decision: Verify OpenCode continuation against the exact coding session

Status: proposed

## Problem

The existing real-model acceptance proves one coding task, but it does not prove that a caller can resume the returned session against the same project and recover usable artifacts.

## Decision

Extend the HTTP acceptance with a second `opencode_run` using the first returned `session_id` as `session`. Require a previously absent `resume.json`, a digest computed from the original report bytes, ordered calculations from the repaired source, unchanged original artifacts and independently rerun assertions. Keep expected outputs on the controller. Keep the template experimental and `tested_on` empty until image build/deploy gates pass.

## API Design

No new runtime API. Acceptance uses the existing `opencode_run(prompt, session, cwd)` contract. `E2E_TOKEN` takes precedence over the existing `ABX_SERVER_TOKEN` fallback for HTTP verifier authentication.

## Alternatives considered

Global `continue_session` can select an unrelated last session. A repeated response marker alone cannot prove session continuity or target-side work. A fake-model protocol pass cannot establish real provider acceptance.

## Dependencies

Pinned OpenCode 1.19.0, Agent Sandbox command/files/shell APIs, and an authorized configured model endpoint for real-model acceptance.

## Test Strategy

Run command regressions and fake-remote protocol tests with actual subprocesses. Reject wrong session ids, incorrect hashes/calculations, missing artifacts and original-file mutations. Run the complete HTTP harness on an owned Express source runtime with a real model and cleanup in `finally`.

## Acceptance criteria

- Existing source repair and independent fixed tests still pass.
- Exact-session continuation produces independently verified artifacts and preserves originals.
- Negative protocol cases fail acceptance.
- Bilingual usage and design docs describe the acceptance and its image/provider limits.
- Real resources are cleaned up; no credentials enter records or public output.

## Evidence

[Clean-wheel verification](../../../evidence/verify/2026-10-16-opencode-session-resume-clean-wheel.md), [earlier recovered-wheel verification](../../../evidence/verify/2026-10-16-opencode-session-resume.md), [issue #17](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/17), [PR #82](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/82).
