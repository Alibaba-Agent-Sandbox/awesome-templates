# Decision: Present nested resource fields as linked human reference tables

Status: proposed

## Problem

The initial field generator dumped complete nested schemas into parent table rows. Those
rows were unreadable despite containing the machine information. The authoring directory
also leaked its _skeleton name into the public resource grammar.

## Decision

Generate one linked section per object or conditional shape. Field rows show type, required
status, default, concise constraints and bilingual purpose. Native component objects retain
an explicit ownership boundary. Schema references link to their actual type sections; no
nested properties/allOf/oneOf JSON is rendered in a parent row. Field meanings are editorial;
structure/constraints/defaults come from the schema and normalizer contract.

Use name:example inside the _skeleton engineering directory. Its smoke lookup and catalog/
design exemption use directory identity. All product resource names obey the same public
rule. The original migration fixture explicitly permits only this skeleton name adjustment.
Pin the Managed Server client to the actually installed final SDK c550 source archive; the
unchanged Guest dependency stays on its published version.

## Alternatives considered

Link only to raw JSON schema: leaves users without a usable field reference. Hand-maintain a
second full property table: drifts from the canonical input shapes. Invent FC/Provider fields:
misrepresents integration. Preserve an author-directory exception in every runtime planner:
adds unrelated public behavior. These alternatives are rejected.

## Dependencies

Canonical resource naming producer is fad843f60881b405cb386537337817e5144892bc. Server source
is c550cf53a9eb0c3c9899d0336b924633eb9b0988, independently built and installed from the official
archive. YAML reader parity is a separately identified follow-up; no custom parser is added
by this readability change. Tracker: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/309.

## Test Strategy

Check complete coverage of all189 property definitions outside conditional selectors, actual
bilingual links/defaults, no nested schema dumps and bounded table rows. Run existing spec,
migration and full scripts suites with the source CLI. Retain all workload/runtime assertions.

## Risks and Limitations

Human purposes need review when new schema fields appear; generation fails on an undocumented
field. Native component internals remain in their owning documentation. Source package version
metadata a7 is not a new PyPI release. Image/cloud verification remains independent.

## Rollback Plan

Revert the presentation/authoring adjustment while retaining producer/source evidence. Do not
restore a public grammar exception or rewrite existing migration and runtime receipts.
