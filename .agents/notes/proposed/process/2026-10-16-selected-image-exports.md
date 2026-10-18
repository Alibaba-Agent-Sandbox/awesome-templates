# Decision: Select image builds without hiding an earlier runtime failure

Status: proposed

## Problem

L1 runner images can advance authorized local daemonless registry transfer and Express tests without cloud credentials in GitHub. Exporting every image or rebuilding every unchanged template for a manual batch wastes storage and runner time. A naive last-commit diff can hide an earlier failed runtime change behind a later docs-only commit.

## Decision

Add dispatch inputs `templates` (default `python-hello`, strict comma-separated catalog whitelist) and `export_images` (default false). Manual runs build only selected names; successful selected images can reuse the common archive/checksum/provenance upload with one-day retention. Automatic PR/main runs default to Pi and python-hello. The public .github/image-export-policy.json supports a temporary, explicitly reasoned all-selected task mode so every successful selected image can advance an authorized changed-image L2 batch. The a361f49 batch produced all 17 archives successfully; this separate closure restores automatic=default without changing that tested Pi head. The flag affects archive saving only, never image selection or build/smoke gates; remove it or set automatic=default after the batch to end this storage expense. This does not depend on unverified dispatch availability. Pull requests use cumulative base-to-head runtime changes; shared image pipeline changes select all products. Main pushes conservatively select all products. A PR that changes only prose/evidence selects no images.

A runtime-changing PR still rebuilds after a later prose-only commit. Avoiding that requires trusted prior successful results keyed by every relevant build input; this change does not invent such proof. Never use only the immediately preceding commit to declare the current runtime verified.

## API Design

No sandbox API change. Workflow dispatch accepts only actual catalog names through environment arguments; no shell evaluation or arbitrary path selection. CI still builds actual images, installs the pinned source wheel through original Docker conditionals, checks the non-root runtime/pins/keyless smoke and uploads selected Docker archives. Provenance includes checkout commit, source head, run ID, SDK commit, base image, local image ID and archive SHA256.

## Alternatives considered

A last-commit-only synchronize diff was rejected during independent review because a runtime failure at A followed by prose-only B could produce a misleading empty gate. Requiring verified input-hash artifacts is a possible later optimization. Cloud credentials in CI and remote registry pushes are unnecessary; transfer/register/test remain local authorized actions.

## Dependencies

GitHub's ordinary PR base/head fields, complete checkout history, catalog/PyYAML, public Docker runner and existing fixed source-wheel preparation. Unknown or unavailable comparison history selects the full catalog. No cloud/model secret is requested by this workflow. The workflow is not yet on the default branch; dispatch availability is NOT VERIFIED until it lands there and an actual manual run succeeds.

## Test Strategy

Pure selection cases plus a real temporary Git repository with runtime A and prose B verify that cumulative selection still includes the changed template. Check manual allowlists/injection rejection, main fallback and every real template context. Local syntax/preparation does not prove remote job execution.

## Acceptance criteria

- Manual single/batch exports build exactly the requested valid templates.
- Runtime/Docker/dependency/smoke changes select their owner; shared pipeline changes select all.
- A later docs-only commit cannot erase an earlier cumulative runtime change.
- Archive export reuses built images, contains no cloud secrets and makes no L2 claim.
- Actual remote runs remain pending until observed; existing PR 82 is unchanged.

## Evidence

[Verification](../../../evidence/verify/2026-10-16-selected-image-exports.md).

Temporary all-selected task mode and its real offline-tool/image prerequisites: [follow-up verification](../../../evidence/verify/2026-10-16-pi-offline-tools.md). The mode must be disabled after the authorized L2 batch; it never marks an unbuilt image verified.

Batch completion and policy closure: [verification](../../../evidence/verify/2026-10-16-image-export-batch-complete.md). This policy/records-only change is stacked separately from the validated Pi head and must be retargeted after its upstream PR lands.
