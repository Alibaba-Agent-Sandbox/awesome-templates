# Decision: preserve structural smoke expectations in v3

Status: proposed

## Problem

Review of [PR141](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/141), [Issue139](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/139), found v3 required string expectations although existing browser/Amp and other catalog smoke commands return structured JSON. Changing only the manifest contract rejects their declared result shapes.

## Decision

Accept explicit string/number/boolean/object/array expectations using the existing express runner comparison. Preserve v3's required expectation key and non-null rule. Existing v2 behavior and evidence remain unchanged.

## API Design

Only schema/template-v3.schema.json smoke.expect types change. No application placement/hooks/limits, runtime, image, credentials or execution changes. Document the stricter v3 expectation-presence migration separately from supported value shapes.

## Alternatives considered

Stringifying dictionaries would change result comparison. Removing the required key or admitting null would relax v3's explicit assertion contract; both remain rejected. A test copying every v2 smoke also exposed omitted expectations; the final regression tests only declared shapes and keeps explicit negative tests for missing/null fields.

## Dependencies

PR141's v3 validator/schema, existing structural express_e2e comparator and pinned scripts/requirements-spec.txt. CLI/runtime consumer Issues remain separate from the specification Issue.

## Test Strategy

Regression first rejected real catalog mappings; corrected schema validates all declared catalog expectation shapes. Missing/null expectations still fail. Run specification/application tests, strict full catalog, bilingual docs/links and whitespace. No cloud test is needed for a metadata-only schema correction.

## Acceptance criteria

Concrete real-catalog regression, no weakening of required v3 assertions, bilingual migration detail and owner verification record. Land the scoped fix through a normal PR into PR141's branch, then review/merge its final current head after all gates.
