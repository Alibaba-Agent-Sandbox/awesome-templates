# Decision: Require actual external OSWorld desktop acceptance

Status: proposed

## Problem

[Issue36](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/36) requests useful screenshot/input/accessibility/task/evaluation inside Express, with actual SDK creation. The existing canonical native smoke does run a real internal desktop task, but PR152's external HTTP callback leaves the desktop opt-in unset. Its6PASS/1GUI SKIP could therefore be labeled full HTTP. A non-model GUI skip is not complete desktop API acceptance. [Review](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/152#issuecomment-6296258528).

## Decision

Canonical --http OSWorld runs always enable E2E_RUN_DESKTOP/E2E_REQUIRE_DESKTOP and record desktop_lifecycle_required without injecting any model credential or changing runtime steps. Require all18current external desktop checks and zero skips; the auditor rejects missing/incomplete fixture coverage. Actually run the unchanged controller against a fresh SDK-created Express native-step sandbox, using owned private exact official asset transport if needed. Preserve historical GUI-skipped/basic/internal-smoke scopes without relabeling.

## API Design

No public runtime command, template version, upstream dependency or image input changes. Only verification behavior becomes stricter. Existing screenshot/click/type/hotkey/a11y_tree/run_task_config/evaluate and private desktop lifecycle stay authoritative. Shared run_steps_e2e.py --http on OSWorld now refuses skipped or partial non-model desktop coverage. Other model skips stay explicitly NOT_RUN; no full VM/benchmark/model-agent/VNC capability is inferred.

## Alternatives considered

Counting internal named smoke as every external API assertion conflates scopes. Optional GUI flags with a green full-HTTP classification conceal the missing gate. Fake PNGs, submitted scores or model response markers do not prove a desktop. Installing GUI dependencies on operator is unnecessary; all desktop tasks run in the owned cloud sandbox.

## Dependencies

Unchanged OSWorldb138d348256078fa634fc3b73567a7337c793e6b, Playwright1.58.0, hash-locked Python graph and pinned Debian critical packages. Reviewed PR152 transport and PR158 manifest-binding fix; exact official native CLI0.4.1 asset digest independently checked against GitHub releasev0.4.1. Optional local OSS controller2.19.1 from repository requirements; temporary private same-account cache contains verified public archives only, with independent cleanup.

## Test Strategy

Regression rejects6PASS/1GUI SKIP even with claimed fixture metadata and accepts18/0only with the actual fixture. A real authored controller subprocess checks both required environment flags and fails closed on a GUI skip. Existing desktop source/process/task/HTTP regressions and shared current-source classifier still pass. Actual external cloud control must upload a fresh HTML/task, get baseline score0, decode real1024x768PNG, send click/Unicode paste/hotkey/click, observe fresh AT-SPI success, get upstream score1 and changed pixels, then clean owned desktop/artifacts and independently remove sandbox/template/cache.

## Acceptance criteria

Required source/spec/docs/current-head CI pass. Current native L1 image and actual SDK-created canonical steps plus all18external GUI checks and independent cleanup have exact receipts. Bilingual qualification, design/catalog and indexed evidence agree; historical skips remain historical. Normal PR merge and all Issue36 criteria before closure. Missing full-VM/benchmark capabilities remain a documented explicit slice, not fabricated provider support.

[Verification](../../../evidence/verify/2026-10-20-osworld-required-sdk-desktop.md).
