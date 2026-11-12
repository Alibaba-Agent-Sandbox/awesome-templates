# Decision: Activate one v1 resource entry and one publication metadata source

Status: proposed

## Problem

Source manifests, managed catalog records, launch tools and documentation still consumed
incompatible public formats and duplicated publication metadata. A key rename alone loses
startup/env/profiles, raw access ports and engineering smoke declarations. The Managed source
image also depends on new runtime behavior absent from its old published client package.
Tracker: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/309.

## Decision

Migrate48 root resources including the author skeleton to specVersion1, with47 source
registry.yaml descriptors and four native managed metadata sidecars. Catalog schema3 retains
only source locators and native resource identities. Registry metadata is the sole current
publication description/version/tag/author source; local resource execution does not read it.

Preserve original smoke/priority/wave as scripts/template-checks.json engineering input,
backed by an immutable original-declaration fixture. Derive default base from the actual
Dockerfile and generation from Provider preparation. Private engineering projection preserves
existing acceptance scripts without emitting a legacy public version. Native steps remain an
independent engineering API; prepared-steps.yaml is not a public runtime resource file.

Admission accepts only v1 and never evaluates native expressions. Numeric expressions stay
intent values until the real CLI native parser and resolved Provider/component validation.
Published v1 field tables are generated from the actual schema. Both README languages retain
their detailed setup and business examples while identifying development-build requirements.
Managed configuration uses native resource role authority and inline state/binding expressions,
with obsolete bindings JSON moved to a clearly engineering-only legacy fixture.

## Alternatives considered

Keep old formats accepted indefinitely: unnecessary unreleased compatibility and ambiguous
ownership. Duplicate Registry metadata in index rows: drift on every update. Add arbitrary
native platform APIs or a general workflow language: unsupported scope. Drop engineering
assertions or raw ports to satisfy the schema: loses existing behavior. Invent protocol
versions for raw ports: makes promises for on-demand listeners. These are rejected.

## Dependencies

Canonical producer is the separately reviewed contract series through
6dfaf3990b43364ea8ec1e2f5a46dc4db2cc0811 (DraftPR310). Generic launch transport semantics are
copied from SDK ab50ad8e750b15221c25ccf231caffdc3f196983 with an exact source lock.
CLI, SDK and Registry consumers must land before the public catalog pin moves. The Managed Server client explicitly pins official SDK source
1079841307f1f63253ae68fdda6e6d2d1e77e851 and the independently observed archive SHA256;
published a7 metadata alone does not identify this new source code. Public release/cloud acceptance remains a separate dependency.

## Test Strategy

Use actual schemas and pure dual-language vectors; preserve original48 workload resource,
startup, readiness, env, services, ports, aliases/profiles and engineering assertions. Check
all metadata locators and both-language declared input names. Exercise the complete local
scripts suite, real source CLI parser/help, current checker and document/reference generators.
Run selected unchanged local HTTP/bridge business controllers without cloud/model credentials.
Record absent full image/model/cloud acceptance independently.

## Risks and Limitations

A valid resource intent is not cloud deployability. Generic independent Sandbox plus Serving
execution still requires a consumer gate. Raw ports do not claim readiness or Gateway exposure.
Historical receipts no longer match a new manifest merely because the workload was preserved;
do not rewrite them as v1 qualification. The final migration is a reviewed source candidate,
not a released CLI/SDK/catalog announcement.

## Rollback Plan

Revert the coordinated migration and catalog pin while keeping original receipts and
engineering fixtures. Do not force mixed v1/old public data into an old consumer. Owned cloud
resources, if any are created by later acceptance, require their independent cleanup evidence.
