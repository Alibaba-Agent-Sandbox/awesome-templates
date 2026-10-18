# Decision: Finish existing template contracts and verify their actual delivery gates

Status: proposed

## Problem

The restored business session had incomplete template migrations, unpublished
working-tree changes and draft PRs. Historical local/source-runtime passes did not
establish current image builds, deployment or the wider product roadmap. Reviews
found marker-only acceptance, process leaks, startup policy/version differences,
catalog drift and missing regression/CI coverage.

## Decision

Complete all 16 existing template v2 migrations and bilingual contracts, retain
historical evidence, and strengthen independent coding and process verification.
Run strict catalog checks including capability agreement. Keep synthetic protocol,
local real-model, Express source-runtime and image/deployment acceptance distinct.
Use Docker-capable GitHub workers for actual image-build validation without
publishing images or sharing cloud/model secrets with those jobs.

The shared source-runtime harness uses per-run random engine socket names. Linux
command wrappers retain the owned session leader until process-group cleanup on
success, error and timeout. Keep Hermes's detached upstream authority boundary
explicit: a CLI deadline does not guarantee cancellation of accepted gateway work.

## API Design

All templates document CLI, Python SDK and direct HTTP POST examples, typed
parameters/defaults/ranges, errors, authentication and execution/client timeouts.
Agents CLI enables only its documented session routes and named version diagnostics
in both startup modes; shell/files stay closed. DeepSeek adds actual file/shell
tools. Qoder and Hermes invoke pinned upstream CLIs. Provider acceptance metadata
remains empty for current versions lacking deployed-image verification.

## Alternatives considered

- Treat SKIP, a response marker or source upload as complete acceptance: rejected.
- Reuse PID-only engine sockets: reproduced cross-process attachment and E2009.
- Kill a process group after reaping its leader: permits an identity reuse window.
- Suppress health/CI failures or promote experimental templates: rejected.
- Leave image builds blocked solely by local Docker absence: use authorized CI.

## Dependencies

- [Template PR](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/82)
- [SDK production command loader](https://github.com/Alibaba-Agent-Sandbox/python-sdk/pull/32)
- Existing per-template Issues linked in the scoped design/engineering records.
- CLI SDK-wheel materialization needs its own owner fix; the image workflow does
  not prove that the CLI deployment pipeline works.

## Test Strategy

Run all template regression suites, the complete local HTTP runner, strict spec
validation, spec/socket tooling, source and record/link/secret scans. Repeat current
Qwen coding and Droid contract checks on real Express with the exact source hashes.
Build the server wheel and compare all 56 Python modules to its recorded Git source.
Inspect actual remote image CI and preserve each missing/failed gate.

## Acceptance criteria

- All existing templates have conformant v2 files, bilingual docs and designs.
- Independent tests reject false coding success and normal-exit descendant leaks.
- Source-runtime evidence includes hashes and cleanup and is not labeled L1/L2.
- Image/cloud/model checks and latest remote CI/review pass before promotion/merge.
- Unimplemented candidate/provider/Skills work remains explicitly open.

## Evidence

[Completion review](../../../evidence/verify/2026-10-16-catalog-completion-review.md).
