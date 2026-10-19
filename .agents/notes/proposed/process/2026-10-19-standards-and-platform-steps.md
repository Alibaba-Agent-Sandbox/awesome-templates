# Decision: Complete contributor standards and add real Express platform-step acceptance

Status: proposed

## Problem

The repository has template contracts but lacks a single comprehensive maintenance
standard and document validation gate. Its Docker-only canonical runner blocks
real template deployment on a controller without Docker, although the CLI offers
platform steps. The user requests all original 64 Issues and their templates,
complete standards, step operations and actual Express verification.

## Decision

Add bilingual project/documentation standards, standalone agent instructions,
translated contribution guidance and executable local Markdown checks in CI.
Generate explicit platform steps from the narrowly supported catalog Dockerfile
profile, embedding only explicit public COPY inputs and preserving pins, ordering,
environment, workdir and non-root user. Extend the existing canonical runner to
select steps, independently poll official READY and preserve all existing external
CLI/SDK and owned-cleanup gates. Keep each real attempt's sanitized outcome and
source provenance. Track every original Issue without equating merge and acceptance.

## API Design

New local commands are `scripts/prepare_steps.py`, `scripts/run_steps_e2e.py` and
`scripts/check_docs.py`; the canonical runner adds `--build dockerfile|steps`.
Existing default behavior remains Dockerfile. Receipts record build mode and
generated-source provenance. Platform ENV arguments are alternating key/value
pairs, as established by a real rejection and successful corrected probe.

## Alternatives considered

Copying source into an existing base remains a diagnostic, not template deployment.
Ignoring COPY would deploy an incomplete product. A general Docker interpreter
would be unnecessarily broad; unsupported constructs fail. Uploading credentials
to Actions is unnecessary for the authorized local cloud operation.

## Dependencies

The actual native CLI template/deploy/info/delete interfaces, official Alibaba SDK
modules and locally installed pinned Python client/server. Cross-owner contracts
remain in https://github.com/Alibaba-Agent-Sandbox/agent-sandbox and
https://github.com/Alibaba-Agent-Sandbox/python-sdk. No SDK/CLI source is modified.

## Test Strategy

Exercise actual reconstructed file bytes/modes, heredocs, unsupported/private COPY
rejection, all current catalog profiles, native/legacy status shapes, mandatory
official READY and existing cleanup regressions. Run strict spec and local docs
checks. Run the actual generated recipes on Express; separate pilot, generated
deployment, Docker L1 and real-model L3 claims. Preserve failed attempts.

## Acceptance criteria

- Complete bilingual standards, navigation, contributor/agent entry points and CI document gate.
- Generated step profiles preserve source and pins; unsupported inputs fail closed.
- Real Express step receipts include external CLI/SDK calls, precise provenance and independent cleanup.
- Every original Issue remains tracked and closes only when all its own criteria hold.
- Current-head applicable CI and required review pass; ordinary PR merge is independently confirmed.

## Evidence

[Verification](../../../evidence/verify/2026-10-19-standards-and-platform-steps.md).
Tracking: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/119.
