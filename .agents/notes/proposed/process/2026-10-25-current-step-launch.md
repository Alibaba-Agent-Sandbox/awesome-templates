# One current launch consumer after native step preparation

Status: proposed

## Problem

Native steps retained a second deployment/create/retry/recovery harness and CLI/SDK creation selector after current launch had already standardized full template startup. Separate callbacks rebuilt application authentication/controller setup. Old native installation and API examples no longer described the current public tool. The controller process monitor buffered 4,096 text characters before recording progress, misclassifying small ongoing logs as idle.

## Decision

Keep genuine native prepare/deploy, asset transport, source hashes, READY polling and owned cleanup. Prepare an idle native template, then reuse the existing current prepared-template consumer: temporary managed manifest with original startup/services/env plus the owned reference, public CLI launch, ProviderSandbox/application client and full HTTP. Delete the duplicate CLI/SDK create selector, optional HTTP bypass, alternate HTTP callback and unused deploy/retry/recovery implementation. Keep only the process monitor actually used by external controllers, with byte-responsive incremental UTF-8 output reads and owned process-group cleanup.

## API Design

run_steps_e2e.py always performs full current application acceptance. The internal native deploy prepares only; public template launch does not gain a build-steps flag or another mode. Native help is checked before asset/cloud writes. Known template IDs are deleted even if inventory temporarily omits them, and absence is independently read back. Failed attempts preserve private recovery staging; successful attempts remove their own staging after evidence. No new state, secret storage or fallback is introduced.

## Alternatives considered

Keeping SDK/CLI creation switches duplicates the public startup contract and can start a different service. Creating a second runner or receipt compatibility upgrader would repeat existing acceptance. Retaining the self-only step_acceptance qualification auditor would reject new hashed-argument receipts or require old-format compatibility; remove it and its mirror tests instead. Existing real source/assets/controller/cleanup checks remain.

## Dependencies

Published CLI 0.5.3, Python client/server 0.4.0a2 and the prepared-template consumer from https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/220. Runtime package/proof cleanup depends on https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/222. This change follows https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/223.

## Test Strategy

Actual subprocesses must keep a small-output job alive across multiple idle intervals, still enforce a wall deadline, and kill descendants after idle or leader completion. Current runner regressions cover native-before-launch ordering, unchanged source manifest, full HTTP, missing controller preflight, failed application, uncertain cleanup and missing-inventory known-ID deletion. Keep current archive/public-launch ownership and digest regressions. Run full applicable CI and a real native step attempt before claiming cloud acceptance.

## Acceptance criteria

- Exactly one current launch consumer follows genuine native preparation.
- No sandbox-create selector, HTTP bypass, old public examples or unused deployment/recovery implementation remains.
- Actual process-progress/descendant regressions and applicable spec/catalog/document/CI gates pass.
- Real current-package step acceptance records full application and independently confirmed sandbox/template/cache cleanup; historical evidence does not certify new runtime.
