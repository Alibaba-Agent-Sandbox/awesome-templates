# Decision: Correct confirmed documentation feedback

Status: proposed

## Problem

The root quick start recommends CLI 0.5.8 or newer while demonstrating source-only deploy/delete entry points, then describes cleanup as kill. Raw-ID cleanup also omits the named deployment’s ownership record.

## Decision

Target the CLI 0.6.0-alpha.0 and Python client 0.5.0a0 previews explicitly, and name the introductory deployment hello. Keep the root quick start to deploy, status, logs and delete; link its business task to the shared guide's existing SDK/HTTP examples. The current CLI removed the old command wrapper, and the existing python-hello package has no OpenAPI binding. Link the CLI's complete explicit-binding guide rather than introducing more configuration files into this repository's quick start. Use its returned Sandbox ID for external application calls and its local name for cleanup. Keep normal interactive confirmation and document retained images/borrowed artifacts. Align the shared guide and root platform-tool names in both languages. Keep this PR Draft until both target releases have actual public readback and this head's required checks pass.

## API Design

N/A — this decision does not involve API changes.

## Alternatives considered

Reverting to old launch/kill commands would undo the requested final CLI surface. Removing the minimum version without selecting the matching CLI contract would still mislead users. Migrating all template-owned API declarations is a separate task; only this root/shared reader path is changed.

## Dependencies

Current CLI deploy, deployment_management and target-first API source at https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/tree/c268608d6a3f917c6d07b7feaa24ab54f25e8fdf. Template runtime, manifests and catalog remain unchanged. The separate offline-CI apt preparation repair has its own decision and verification.

The CLI [release preparation PR271](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/pull/271) and Python [release preparation PR174](https://github.com/Alibaba-Agent-Sandbox/python-sdk/pull/174) own the target candidates. Preparing these installation examples does not prove either candidate is public. Their actual package publication/readback is a merge dependency.

## Test Strategy

Check changed Markdown links, bilingual wording, seven-section note structure and git diff hygiene. Inspect the exact merged CLI source and exercise its built executable's relevant help contracts. Use existing owner documentation gates where available. Runtime, image, deployment and model behavior are unchanged, so this prose correction does not require new cloud resources.

## Acceptance criteria

English and Chinese quick starts select the exact preview versions, use one named deployment and accurate cleanup, and pass local document checks. The 0.5/0.6 CLI boundary and explicit OpenAPI-binding requirement are clear. Both target packages have actual public readback and required remote gates pass before this PR becomes ready and merges; no new cloud acceptance is claimed.

## Evidence

[Local documentation verification](../../../evidence/verify/2026-11-25-confirmed-documentation-feedback.md).

[Current CLI command guidance](../../../evidence/verify/2026-11-25-current-cli-template-guidance.md).
