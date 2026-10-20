# tau2-bench

## Purpose

Run and independently evaluate an original Tau2 text retail task through named
commands, preserving native agent/user interaction and task data rather than a
replacement benchmark. Refs [Issue59](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/59).

## Capabilities

Shell, files, code and port9000. Fixed v1.0.1 retail source supports task discovery,
bounded original model execution, downloadable sanitized trajectories and keyless
strict replay through the original evaluator. Other domains, voice, knowledge
tasks and nonempty natural-language judge assertions are outside this slice.

## Exposed API

[Command reference](../../tau2-bench/README.md#command-reference) defines all four
commands and types/defaults/bounds. `tau2_version` and `tau2_setup_check` are
non-model inspection. `tau2_run` accepts domain/task/step/deadline parameters and
returns native reward, counts and owned artifact metadata. `tau2_verify_artifact`
accepts a required workspace path plus task ID and returns native strict replay.
Fixed argv is `/opt/tau2-venv/bin/python /home/user/app/worker.py <operation>`;
validated inputs and model settings use anonymous stdin. The worker invokes
original `get_tasks`, `TextRunConfig`, `run_single_task`, `SimulationRun` and
`evaluate_simulation(..., strict_replay=True)`. Source version is read from the
verified source tree rather than invented distribution metadata.

## How to build

[Dockerfile](../../tau2-bench/Dockerfile) retains Alibaba FC base, non-root `user`,
no CMD/ENTRYPOINT, rootfs8GiB guard, immutable server source and an isolated native
venv. [upstream.json](../../tau2-bench/upstream.json) pins official source
fc0055dc4e0a316c3f83133267fbd6faaa770992, measured archive size/digest. Installer
rejects traversal/links and selects only source, license and retail data.
[requirements.lock](../../tau2-bench/requirements.lock) is a frozen export of the
unchanged original uv.lock, enforced by pip `--require-hashes` and `pip check`.
The complete frozen export is retained as `requirements.upstream.lock`;
`select_lock.py` evaluates original markers for Linux CPython3.13 and removes only
inactive entries/active marker syntax without changing pins or hashes. The image
asserts Python3.13. The strict checker deliberately accepts only this selected
plain hash lock; its policy is unchanged.
Modern uv `--locked` export reported upstream lock staleness; it did not pass and
no dependency update was resolved. Native CLI steps reuse the same installer and
verified parallel/owned OSS transport; immutable source must be committed first.
Start: `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`.
Ready: `agent-sandbox-server healthcheck --port 9000`.

## Express feasibility

Feasible: slice

Limiting factor: the requested CPU-only text retail subset excludes other domains,
voice/knowledge runtime dependencies and natural-language judge tasks.

2 vCPU,2048MiB RAM, non-root, no Docker/KVM/GPU/extra capabilities, about10GiB
rootfs and explicit model egress. Both native participants require a configured
compatible model. Actual image, memory sufficiency and Express execution remain
pending measured verification; a design feasibility statement is not a pass.

## Risks

Both participants incur model costs. Model URL/key/model must be explicit; no
implicit vendor fallback. Isolated environment excludes cloud/GitHub credentials.
Key and endpoint are recursively scrubbed before retaining trajectory; private
native logs/HOME/processes are removed. Owned successful artifacts remain for
caller inspection; partial failures are removed. Output/deadline/path bounds,
serialized group ownership and pidfd cleanup protect unrelated work. Replay is
keyless and rejects source/task/reward mismatches. Preserve original MIT and
wrapper Apache2.0 notices. Source checksum is measured, not published upstream.

## Test plan

L0: process/validation/controller regressions, strict spec and bilingual links.
L1: actual image install, locked dependency check and version/task-count114 smoke.
L2: SDK-created canonical native steps, official READY, CLI/native version and full
HTTP suite; independently verify owned sandbox/template/asset cleanup.
L3: original retail task0 with real agent/user, complete termination and reward1.0,
original tool messages, independently downloaded trajectory/hash, separate keyless
strict native replay, post-return unpredictable acknowledgement and artifact
absence. Public controller requires actual SDK and refuses local-model acceptance;
`ABX_E2E_OK` alone cannot establish a pass. L4: no untested provider claims.
