# Decision: Run current-source L1 image builds on public GitHub runners

Status: proposed

## Problem

Local validation has no Docker engine, so it cannot establish image acceptance.
GitHub Ubuntu runners can build images without cloud or model credentials. The
existing local e2e workflow installs host CLIs and cannot detect image-specific
runtime dependencies, including agents-cli's missing Node>=22 requirement.

## Decision

Add an independent image-build workflow for pull requests, main pushes and manual
runs. Cover all16product templates with fail-fast disabled and at most4parallel
jobs. Checkout public server-sdk commit e2cb27e24fde0a67112f82b8d44af463445a5d1a,
build its wheel and copy the exact wheel into each isolated template context.
Replace only FROM region/tag placeholders with cn-hangzhou/v0.0.49. Preserve the
original SDK install conditional; no production CLI Dockerfile rewrite is copied
or simulated. Build actual images with plain progress and no image push, cloud
credentials, model credentials or .env input. Validate the non-root image user,
installed version pins and declared keyless commands in a network-disabled local
container, with the entrypoint explicitly overridden for this L1 check.

Normalize Amp's SDK install to the same COPY/conditional wheel path as the other
templates. Fix agents-cli's image runtime by copying the reviewed OpenClaw
SHA256-verified official Node24.16.0 installer and update bilingual stack/design.
Qwen0.23.0 declares Node>=22; the Alibaba base's Node20 is insufficient. Host CI
Node24must not conceal this image prerequisite.

## API Design

No public named-command/API changes. New workflow image-build.yml is a distinct
L1gate. Its local-container smoke is not provider deployment, abx materialization,
L2or genuine model/coding acceptance. Existing local CI remains unchanged.

## Alternatives considered

Treating the absence of local Docker as permanent inability to advance L1would
leave an available public runner unused. Rewriting SDK RUN instructions in the
CI context would conceal the separately reproduced production CLI physical-line
rewrite defect. Pushing images or using cloud credentials is unnecessary for L1.

## Dependencies

Public Alibaba base image v0.0.49, GitHub Ubuntu24.04Docker runner, public pinned
python-sdk source, upstream pinned installers and network access during builds.
The source-wheel install path matches DockerBuilder.injectSdkWheel: pip wheel
server-sdk --no-deps and copy the resulting wheel to the template context root.
The production CLI rewrite defect remains owned by agent-sandbox; this gate does
not assert that defect is fixed.

## Test Strategy

Before remote execution, parse workflow YAML, compare the matrix with all16catalog
entries, validate shell/embedded Python syntax, check the wheel COPY branch exists
and run affected template conformance/link/diff checks. These are preparation
checks only. Remote docker build and installed-pin/keyless-container results must
actually pass before recording L1. Preserve the per-template build/runtime logs.

## Acceptance criteria

- Independent16-template L1matrix, max-parallel4, no duplicate feature-push run.
- Fixed public SDK wheel is installed through original template conditionals.
- Only FROM placeholders are rewritten; .env and host credentials are excluded.
- Build/installed-pin/non-root/keyless checks execute against actual Docker images.
- No push or provider/model acceptance is inferred; remote failures remain failures.
- Root contribution workflow publishes and observes real CI before claiming L1.

## Evidence

[Preparation and pending remote validation](../../../evidence/verify/2026-10-16-template-image-build-gate.md).
