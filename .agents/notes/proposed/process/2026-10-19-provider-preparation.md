# Decision: Keep preparation owned by each provider

Status: proposed

## Problem

Issue118 requires replacing catalog hints that suggest manually carrying cloud IDs
between providers. A displayed hint or launch command cannot prove native preparation
or backend acceptance, and missing terminal/code capabilities must remain unsupported.

## Decision

Use provider-preparation-required prerequisite hints consistently for all catalog
sources. Document the source-directory authority and provider-owned image/base/
registration adaptation in both languages. When automatic preparation exists, its
implementation belongs to the selected provider. The hint itself declares no such
implementation or provider pass. Retain actual Verified/tested_on/status evidence.

## API Design

Only the existing optional catalog providers-map values and documentation change;
schema-version1 clients already ignore that extension. No SDK or CLI endpoint,
capability, ID conversion or native launch protocol is introduced here.

## Alternatives considered

Cross-cloud template-ID conversion has no valid ownership contract. Silently dropping
missing terminal/code requirements would change the product. Marking preparation hints
as verification would create false certification. All three are rejected.

## Dependencies

https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/118.
Runtime capability/preparation implementations remain in their independent provider
and SDK owners, linked using absolute GitHub URLs in the bilingual guide.

## Test Strategy

Strict catalog/spec conformance, bilingual/local-link checks and a behavioral checker
regression confirm that a preparation hint without real receipts cannot certify a
template. Existing source/runtime acceptance boundaries remain intact.

## Acceptance criteria

- Source authority and provider responsibility are clear in both languages.
- Missing capabilities remain unsupported; no cross-cloud IDs or unrun native passes.
- Catalog/spec/docs regressions and current-head checks pass.
- Engineering evidence is included; ordinary PR merge is confirmed before Issue closure.
