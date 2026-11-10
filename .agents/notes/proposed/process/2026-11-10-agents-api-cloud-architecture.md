# Decision: Explain the managed Agents deployment architecture

Status: proposed

## Problem

The Registry details show the template README, which names FC and PostgreSQL but
does not give readers a clear module-to-cloud-service map or a compact list of
resources to prepare. The user requested that overview on the agents-api page.

## Decision

Add aligned architecture, task flow, module/service mapping and resource ownership
tables to both template READMEs, under the existing Stack heading. Include a
self-contained SVG under docs/assets and use its absolute public raw URL because
the current Registry renderer does not rewrite image sources or render Mermaid.
Keep the diagram focused on the runtime; explain ACR, RAM and optional networking
in the tables. Align the design description and its obsolete dependency paragraph
with the unchanged public recipes.

## API Design

N/A — this decision does not involve API changes.

## Alternatives considered

- Mermaid alone becomes a code block in the current Registry renderer.
- A relative image URL resolves against the detail page and returns 404.
- A Registry rendering change is unnecessary for this template documentation task.
- A diagram inside the template directory would add an image-build context input;
  this explanatory asset belongs under docs/assets.

## Dependencies

The existing template at e94ab308a74715982bb059b142518f7d6070c1c2,
CLI 0.5.10, and Python client/server 0.4.0a7 establish the documented architecture.
The Registry renderer at 1601d5e5c2dc9d0afed3a67cc974a8c43ac09e0e
selects the corresponding README language and preserves absolute image sources.
No runtime, manifest, catalog, provider or package change is required.

## Test Strategy

Independently inspect the template and published runtime/CLI before writing.
Check Gateway-to-database admission, timer-based dispatch, FC asynchronous Worker
invocation, Session-owned Sandbox execution and database-backed file storage.
Run documentation links, strict template checks, existing documentation-checker
regressions, bilingual review and the actual Registry Markdown renderer. Inspect
an SVG preview and verify public asset/page availability after the normal merge
and synchronization workflows. No cloud resources are needed for this prose change.

## Acceptance criteria

- Readers can identify each runtime module and its cloud product or service.
- Required existing resources, conditionally needed resources and automatically
  deployed resources are distinguished, including database and network ownership.
- The diagram renders in Registry and the text tables remain readable without it.
- Existing template behavior, configuration examples and acceptance claims remain
  unchanged; no unexecuted cloud or model validation is claimed.

## Evidence

[Verification](../../../evidence/verify/2026-11-10-agents-api-cloud-architecture.md).
