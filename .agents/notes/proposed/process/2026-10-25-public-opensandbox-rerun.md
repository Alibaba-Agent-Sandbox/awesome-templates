# Decision: Rerun public template launches without substituting source-only image evidence

Status: proposed

## Problem
A fresh developer must install public tools and use the documented catalog path. A source-built historical CI image is insufficient evidence for that path. Rebuilding the same image again for a second backend adds cost without improving provenance.

## Decision
Run the existing published-package OpenSandbox launch matrix against the default public Git catalog and publicly fetched pinned provider. Optionally export only its unique launch-owned image after successful application assertions, before independent cleanup. A separate Express prepared-image run must retain that boundary. Preserve failed attempts and native provider identities.

## API Design
N/A — this decision does not involve product API changes. The verification runner accepts optional `--export-image-dir`; manual CI accepts `export_images`.

## Alternatives considered
Reuse the old source-pinned image matrix: rejected as a substitute for current public CLI preparation. Silently translate foreign managed template IDs: rejected because these are provider-owned identities.

## Dependencies
Published CLI 0.5.1, client/server 0.4.0a1, the selected public provider commit, Docker-backed original OpenSandbox and an owned disposable registry.

## Test Strategy
Unit ownership rejection, complete specification checks, real published matrix including CLI/Python/host HTTP expected outputs, authentication, source identity, file round trip and independent owned-resource absence. New attempts retain separate receipts.

## Acceptance criteria
- All 46 source entries use fresh public-package installs and default Git resolution.
- Export hashes and exact provenance correspond to only this successful launch image.
- Native managed identity applicability is explicit; no cross-provider substitutions.
- Runtime outcomes, cleanup and UX findings remain separate and reproducible.

## Evidence
https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/215
