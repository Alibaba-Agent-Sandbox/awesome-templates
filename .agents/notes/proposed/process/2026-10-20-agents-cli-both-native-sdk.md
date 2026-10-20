# Decision: Independently verify both native Agents CLI adapters through SDK

Status: proposed

## Problem

[Issue25](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/25) covers both installed Codex and Qwen Code behind the restricted local session API. The existing owned SDK controller only selects Qwen, and its historical image/model result does not certify the current2.0.1profile or Codex. Source fixtures cannot replace actual native model turns.

## Decision

Add an explicit --adapter choice (qwen-code default, or codex) to the existing owned-cloud SDK controller, preserving its independent source/artifact/test/held-out/nonce-cleanup gates. Each selected adapter creates a fresh sandbox and journal, chooses the exact requested native backend and reports its own result. Explicitly choose the image's pinned Node24 PATH for the new model-configured server rather than inheriting an operator PATH. Keep product runtime/API/version/policy/dependencies unchanged.

## API Design

Only verifier CLI gains --adapter; existing default invocation stays Qwen-compatible. Reject unknown adapter before HTTP/resource creation. The local session request selects that adapter, retains explicit model/workspace and polls original server state. Actual provider-native SDK management seeds and verifies source out of band, while the original public policy continues denying generic shell/files/process routes. The verifier never turns those endpoints on. Reports describe owned-template scope rather than guessing image build mode; outer canonical template ownership supplies build provenance.

## Alternatives considered

A Qwen success cannot certify Codex, a version response cannot prove a model edits code, and a response marker cannot establish source/test correctness. Changing runtime policy or adding unrestricted public management routes is unnecessary. Reusing shared/important sandboxes or running generated source on operator violates ownership and isolation. Inventing a vendor key or endpoint is excluded.

## Dependencies

Unchanged Codex0.162.1, QwenCode0.23.0, SHA256-pinned Node24.16.0, template2.0.1/servere2cb27e and original restricted policy. Actual operator native SDK source d4d93e8cbb986f33a8868f7a4139ed0edb49eaba. Existing approved OpenAI-compatible endpoint/key/model only. Actual native step/image/SDK/cleanup proof still required; no model/vendor capability is inferred from mocks.

## Test Strategy

Existing independent baseline/source/artifact/original/generated-test/held-out negative controls, premature-exit/skip/pycache rejection and exact nonce-owned cleanup tests remain. New HTTP fixture verifies both requested adapters reach the real session payload and invalid adapter fails before networking. Selected Node PATH/credential allowlist is tested without inheriting host credentials. Then actual current-source canonical deployment and native SDK model run for each adapter must pass independently, including separate completed-turn persistence and cloud absence.

## Acceptance criteria

Source/spec/docs/current-head CI pass; actual native L1 and current Express SDK-created canonical CLI/SDK smoke pass. Each of the two original native adapter models changes seeded source, creates artifacts and passes independent original/generated and six held-out evaluations in a fresh owned cloud sandbox. Original restricted public policy stays enforced and cleanup independently verifies exact ID/nonce absence. Bilingual records/qualification and normal PR/main merge before Issue25closure. Missing/failing native models remain explicit.

[Verification](../../../evidence/verify/2026-10-20-agents-cli-both-native-sdk.md).
