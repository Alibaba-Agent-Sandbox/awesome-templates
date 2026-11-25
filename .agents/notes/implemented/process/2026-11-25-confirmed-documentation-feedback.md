# Decision: Correct confirmed documentation feedback

Status: implemented

## Problem

The root quick start recommends CLI 0.5.8 or newer while demonstrating source-only deploy/delete entry points, then describes cleanup as kill. Raw-ID cleanup also omits the named deployment’s ownership record.

## Decision

Target the CLI 0.6.0-alpha.1 and Python client 0.5.0a0 previews explicitly, and name the introductory deployment hello. Keep the root quick start to deploy, status, logs and delete; link its business task to the shared guide's existing SDK/HTTP examples. The current CLI removed the old command wrapper, and the existing python-hello package has no OpenAPI binding. Link the CLI's complete explicit-binding guide rather than introducing more configuration files into this repository's quick start. Use its returned Sandbox ID for external application calls and its local name for cleanup. Keep normal interactive confirmation and document retained images/borrowed artifacts. Align the shared guide and root platform-tool names in both languages. Both target releases now have actual public readback. The final records-only head still requires its own checks and a normal PR merge.

## API Design

N/A — this decision does not involve API changes.

## Alternatives considered

Reverting to old launch/kill commands would undo the requested final CLI surface. Removing the minimum version without selecting the matching CLI contract would still mislead users. Migrating all template-owned API declarations is a separate task; only this root/shared reader path is changed.

## Dependencies

The reviewed deploy, deployment_management and target-first API contract source is at https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/tree/c268608d6a3f917c6d07b7feaa24ab54f25e8fdf. Template runtime, manifests and catalog remain unchanged. The separate offline-CI apt preparation repair has its own decision and verification.

The CLI [alpha.1 release](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/releases/tag/v0.6.0-alpha.1) and Python [0.5.0a0 client/server pair](https://pypi.org/project/agent-sandbox-client/0.5.0a0/) have actual public artifact readback and fresh-consumer evidence. The withdrawn alpha.0 remains historical and is not recommended. The final public-prerequisite receipt below distinguishes root execution from this record review.

## Test Strategy

Check changed Markdown links, bilingual wording, seven-section note structure and git diff hygiene. Inspect the exact merged CLI source and exercise its built executable's relevant help contracts. Use existing owner documentation gates where available. Runtime, image, deployment and model behavior are unchanged, so this prose correction does not require new cloud resources.

## Acceptance criteria

English and Chinese quick starts select the exact preview versions, use one named deployment and accurate cleanup, and pass local document checks. The 0.5/0.6 CLI boundary and explicit OpenAPI-binding requirement are clear. Both target packages have actual public readback and required remote gates pass before this PR becomes ready and merges; no new cloud acceptance is claimed.

## Evidence

[Final public-package prerequisites](../../../evidence/verify/2026-11-25-template-guidance-public-prerequisites.md). Earlier dated checkpoints below retain their original results; they are not current publication blockers.

[Local documentation verification](../../../evidence/verify/2026-11-25-confirmed-documentation-feedback.md).

[Current CLI command guidance](../../../evidence/verify/2026-11-25-current-cli-template-guidance.md).

[Alpha.1 prerequisite and landed image-source integration](../../../evidence/verify/2026-11-25-cli-alpha1-template-guidance.md).
