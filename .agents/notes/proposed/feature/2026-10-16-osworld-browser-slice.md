# OSWorld browser desktop slice

Status: proposed

## Problem

[Issue 36](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/36) explicitly requests the feasible non-KVM computer-use slice. Its full benchmark and provider acceptance remain open. Official OSWorld also has a container desktop adapter; a VM-only blanket blocker does not describe this narrow workload.

## Decision

Add an independent Alibaba Debian 13 template using fixed OSWorld source b138d348256078fa634fc3b73567a7337c793e6b, real Xvfb/Openbox/DBus/Chromium, typed native PyAutoGUI actions and private-clipboard Unicode paste, the upstream screenshot and AT-SPI handlers, and selected unchanged upstream getters/metrics. Foreground xclip receives text on stdin, then releases its owned selection and exits after actual Ctrl+V. Input targets only the owned browser main window by its exact launched PID. No upstream arbitrary-code HTTP listener runs: Flask's internal test client invokes only observation handlers.

A private worker owns one desktop session. The server pins the unreaped session leader until its process group has stopped. Startup failure, deadline, Python cancellation and stop clean the group and private profile. This Linux process-group boundary does not contain a child that deliberately creates a new session. HTTP disconnect is not cancellation. No model/cloud credentials, inherited display or user profile enter the worker. HOME is preserved; private XDG paths, Xauthority and Chromium user-data-dir isolate the session, with Python user-site loading disabled.

Upstream's Linux accessibility handler unconditionally probes LibreOffice. This browser slice represents an absent Office version with an empty tuple; it fabricates no binary or version and rejects Office tasks. The original vendored file remains unchanged. Selected pure definitions are compiled from the fixed packaged source without importing the framework's cloud/proxy/Office registry.

## API Design

See [design](../../../../docs/design/osworld.md) for signatures. `screenshot`, `click`, `type`, `hotkey`, `a11y_tree`, `run_task_config` and `evaluate` operate on one explicitly started session. Only `chrome_open_tabs` and bounded `sleep` setup, `accessibility_tree` result, `rule` expectation, and `check_include_exclude`/`exact_match` metrics are supported. Validate the whole submitted task before any setup. Unknown setup, VM, Office, proxy, arbitrary launch/shell, postconfig and unsupported evaluators fail rather than receive a score.

## Alternatives considered

- Full VM/benchmark: Express has no KVM; its snapshot lifecycle and complete app/evaluator suite are outside this slice.
- Exposing upstream `/execute`: unnecessary arbitrary-code HTTP surface and private input in child argv.
- A screenshot-only stub or response marker: insufficient evidence for real actions or evaluation.
- Importing upstream setup/metric registries: invokes unrelated dotenv/proxy paths and large Office/cloud dependencies.

## Dependencies

Pinned source and Apache-2.0 license are under `osworld/upstream`. Python requirements include a complete hash lock; Playwright 1.58.0 selects its browser revision. Critical Debian packages have exact versions; their transitive system security dependencies remain repository-resolved. No new provider or SDK contract is introduced. The source server wheel is handled by the existing L1 pipeline. The worker must preserve PLAYWRIGHT_BROWSERS_PATH so its safe environment allowlist resolves the image-installed Chromium rather than a user cache. Initialization errors identify only fixed phases and exception classes, omitting paths/input.

## Test Strategy

Real process regressions cover normal stop, unexpected leader exit, redirected descendants, timeout, malformed output, cancellation, foreign process preservation and private state/environment. Canonical and direct HTTP startup test auth/types/registration. The actual desktop smoke captures PNG and AT-SPI, verifies baseline evaluator 0, sends real mouse/keyboard events, independently reads browser state, then requires evaluator 1 and changed pixels. Missing GUI cannot pass the required functional gate.

## Acceptance criteria

- [x] Strict v2 conformance, bilingual usage, design and accurate experimental catalog.
- [x] Scoped process/task/HTTP regressions and final native source functional check pass.
- [ ] Actual non-root, network-disabled image build/smoke pass on the submitted head.
- [ ] Actual Express changed-image SDK/HTTP/CLI acceptance and owned cleanup pass.
- [ ] Review and normal PR delivery complete.

These criteria cover only the browser slice. Full OSWorld benchmark/model tasks remain unimplemented and Issue 36 must stay open.

The screen/viewport distinction and latest failed image run are tracked in [viewport follow-up](../../../evidence/verify/2026-10-16-osworld-viewport.md); real image/provider acceptance remains pending.

The third actual image smoke exposed a non-root WORKDIR ownership defect; [workspace follow-up](../../../evidence/verify/2026-10-16-osworld-workspace.md) preserves the failed run and the necessary Docker ownership correction.
