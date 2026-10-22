# Decision: Qualify every source template on both requested image backends

Status: proposed

## Problem

Issue185 requests complete current-source Express image and OpenSandbox runtime
acceptance. Existing strict evidence covers18 Express image runtimes,17 complete
image HTTP controllers and no OpenSandbox source runtimes; steps46/46 are separate.

## Decision

Reuse exact-source image builds and the canonical Express transfer/cleanup runner.
Require owned non-model native fixtures consistently. Add an explicit keyless
workflow option to exercise each selected image on the original OpenSandbox
Docker server through real SDK and complete HTTP operations, with independent
container and process cleanup. Preserve all historical evidence and failures.

## API Design

No product API changes. Add workflow `test_opensandbox` and a source runtime
controller. Generic OpenSandbox code.interpret remains explicitly unsupported;
the existing CLI capability gate remains authoritative and unchanged.

## Alternatives considered

Do not substitute steps, managed interpreter, mock, version-only or Docker build
results. Do not forward Express credentials to Actions or OpenSandbox.

## Dependencies

Original OpenSandbox30348cbd, provider9d2cf074, CLIc8e8ad78, SDK33f857f5;
template-specific immutable server source and existing Dockerfile build contract.

## Test Strategy

Real subprocess fixture/skip regressions, existing image/cleanup tests, spec/link
checks and current-head CI. Pilot native jobs before the complete46 matrix.
Express uses actual native registration and private registry/sandbox cleanup.

## Acceptance criteria

All46 current sources have qualified Express regular image runtime/full HTTP
and native OpenSandbox named API/full HTTP receipts with independent cleanup.
No model/account claim is expanded; blockers and failures remain explicit.

## Evidence

[Verification](../../../evidence/verify/2026-10-22-source-image-backend-acceptance.md).
[Issue185](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/185).
