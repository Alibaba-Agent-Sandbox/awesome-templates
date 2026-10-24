# apply-patch

## Purpose

Expose the actual official Codex file-patching dialect as a small model-free named tool.

## Capabilities

Native add/update/move/delete with bounded process lifecycle, no shell/patch argv, relative workspace paths and real byte verification. No inference, Rust build, GPU, KVM or Docker. Caller file mutations persist; owned smoke artifacts are removed.

## Exposed API

apply_patch(patch_text: str required <=256KiB, cwd: str="") -> {stdout,stderr,exit_code}; cwd must be an existing WORKSPACE subdirectory. apply_patch_version() -> actual native version. apply_patch_smoke() -> APPLY_PATCH_OK after actual add/update/move/delete/literal bytes and owned cleanup.30-second patch deadline/256KiB per stream. Typed schema coercion is inherited from the SDK; nonzero native errors stay nonzero results.

## How to build

[Dockerfile](../../apply-patch/Dockerfile) installs locked official @openai/codex0.162.1/native package integrity with npm ci, validates the actual binary and makes its supported apply_patch argv0 alias. Official release source092d3acd6bec3e3a14bdc7e7a2810ab628ab759d is identified, not locally rebuilt. Retain upstream Apache-2.0 LICENSE. Alibaba base v0.0.49, generation2 start_cmd `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`, ready_cmd `agent-sandbox-server healthcheck --port 9000`, non-root2vCPU/2048MB, pinned server wheel/archive.

## Express feasibility

Feasible: yes

Limiting factor: none for native patch execution; official Linux x86_64/aarch64 binaries avoid a heavyweight Rust build. Actual image/cloud acceptance remains required.

## Risks

Patch failures may leave partial edits. Reject every file/move path escape before execution, but preflight is not a same-user concurrent-race security boundary. No configured model/cloud secrets are inherited. Native parser receives a private file rather than shell text. Cleanup holds the original leader with WNOWAIT until its group is stopped.

## Test plan

L0 actual official native parser over HTTP, add/update/move/delete, literal/Unicode content, malformed patch errors, files API bytes/absence, missing/undeclared/unknown args. Real process deadline/output/descendant controls and path/symlink negative controls. L1 locked packages, actual version and smoke as non-root. L2 real steps/deploy READY, CLI+SDK smoke and full external HTTP artifacts, independent owned cleanup. L3 not applicable (no inference); L4 unrun.

Release readiness 1.0.1: align default and injected server SDK source to `e2cb27e24fde0a67112f82b8d44af463445a5d1a`; preserve historical receipts and require new image/workflow acceptance.
