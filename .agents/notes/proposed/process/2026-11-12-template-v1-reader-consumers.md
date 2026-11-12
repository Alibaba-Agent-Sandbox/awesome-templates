# Decision: Read v1 source files with the shared Core profile

Status: proposed

## Problem

Python SafeLoader interpreted unquoted on and date values differently from the Node source
reader. Schema validation could consequently reject the same v1 resource in one consumer.
The Managed Server also needs the actual SDK Session projection changes, beyond the earlier
c550 image baseline.

## Decision

Use the canonical ef695 shared YAML reader at every template, publication metadata and
catalog source-file entry owned by this repository. Bound file reads before parsing. Keep
non-source YAML serialization and unrelated workflow fixtures on their existing library.
Checkers validate intent without reading env files or evaluating Devs expressions. CI installs
the exact small yamlcore dependency already pinned by the canonical owner.

Pin only the Managed Server client to the immutable official SDK b988 source archive with
its verified SHA256. Preserve the Guest published a7 dependency and existing image evidence.
Clarify the supported credential choices, separate model bindings from instance env, and
correct Managed ingress documentation to existing exclusive HTTPS Gateway routes. Extra
resources remain a CLI preflight responsibility; generic schema ownership is unchanged.

## Alternatives considered

Patch PyYAML scalar resolvers independently in each script: repeats policy and diverges from
actual library semantics. Switch all YAML uses: changes unrelated consumers. Keep a public
source recipe on old c550 after the API projection: fails to deliver the new observable API.
Rebuild Guest or repeat cloud matrices for reader-only changes: adds no relevant evidence.

## Dependencies

Canonical producer ef695803cb78bf82b8473195fcb37b3e6357a363 (Draft310). SDK source
b988d2a76057b6202d836ec329cc0bd90a572b26 (Draft164) contains the shared reader and
actual Session projection. Tracker: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/309.
Cross-repository release, real deployment and domain preflight remain coordinated consumer gates.

## Test Strategy

Execute all shared raw vectors through bounded actual filesystem reads, then exercise the
actual resource checker, metadata and catalog consumers with on/date strings and a process
environment canary. Run the complete owner scripts suite, specification/catalog/doc checks,
generator drift check, scoped lint and whitespace check. Independently install the exact
final SDK archive with managed-agents extras, inspect provenance and run its reader vectors.

## Risks and Limitations

The format intentionally admits a JSON-compatible Core subset, not every YAML conversion.
Source parsing does not prove native Devs evaluation type preservation or cloud support.
The source distribution still identifies itself as a7 and is not a new PyPI release. Final
Server image and cloud/model evidence must identify their own exact input bytes.

## Rollback Plan

Revert the owner consumer/pin increment and keep prior canonical/source/image records intact.
Do not silently restore parser disagreement or relabel historical receipts as new acceptance.
