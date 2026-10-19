# Decision: Separate managed runtime entries from source build contexts
Status: proposed

## Problem

Issues31/32 specifically request catalog-only managed base/code-interpreter-v1 entries, but their copied source-template checklist assumes repository-owned Dockerfiles. Manufacturing a source deployment would verify another resource.

## Decision

Use additive managed_templates catalog namespace and complete bilingual per-entry documentation. No fabricated source directories, pins, named commands or native interpreter claims. Preserve existing source selectors unchanged.

## API Design

Managed entry fields describe provider/template ID, docs/evidence and scope. Reproducible verifier uses actual native SDK, CLI exec, runtime inventory, run_code fallback observation and independent paginated cleanup. It never deploys/deletes a managed template definition.

## Alternatives considered

Adding managed IDs to source paths breaks independent source install/build. Treating SDK fallback as native Jupyter acceptance is false. Leaving catalog-only entries undocumented hides runtime differences.

## Dependencies

Existing Alibaba account, verified native CLI0.3 and paired SDK. No credentials are published. Source standards depend on PR121; no SDK/CLI changes needed.

## Test Strategy

Actual CLI+SDK runs for both IDs, genuine inventory, output42, SDK file roundtrip/removal, independent owned sandbox absence; doc/spec checks. Source L1/L2 are inapplicable to provider-owned definitions.

## Acceptance criteria

Bilingual docs, scope-bearing catalog entries and genuine runtime receipts; passing current-head CI and ordinary merge. Original generic source-deploy checklist remains distinguished from specific catalog-only scope rather than falsely marked run.
