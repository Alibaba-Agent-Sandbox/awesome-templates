# Complete workflow reference validation

Status: proposed

Issue: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/197

## Problem

Managed catalog validation accepted an application operation absent from its
declared service, and accepted service bindings on exec/interpreter workflows.
It also accepted exec startup without a command. Source template validation
rejected these combinations. The closed v4 schema
also accepted an unused legacy local runtime profile, contrary to the project's
unreleased, no-compatibility policy. The bilingual specification still described
retired managed catalog fields.

## Decision

Use one schema-validated workflow-reference checker for source and managed
inputs. It validates the default workflow, application service and provided
operation, rejects service bindings on other workflow kinds, and requires an
explicit command for exec startup. Managed records have no command field, so
commandless exec startup is rejected. Keep source port checks and managed input
checks in their respective owners.
Remove the unused legacy profile rather than translating it. Document the exact
current managed fields and distinguish historical evidence from certification.

## API Design

`validate_workflow_references(data)` operates only after the caller's complete
schema validation and returns errors without I/O or execution. Both existing
entry points call it; no new user-facing compatibility mode is introduced.
Only `server-core-agents` remains a local application runtime profile.

## Alternatives considered

Duplicating the source reference checks in the managed checker would recreate
the drift that caused this defect. Keeping or renaming the unused legacy input
would retain unsupported configuration without an actual consumer.

## Dependencies

The existing v4 source schema and workflow-portion schema remain authoritative.
There are no SDK, runtime, image, provider, dependency or catalog-content changes.

## Test Strategy

Demonstrate rejection regressions before the implementation fix, then run both
source/managed/application suites, image-selection regressions, specification
tools, all-template checks, managed catalog checks, documentation and diff checks.
No image or cloud qualification claim is added by these checker/schema fixes.

## Acceptance criteria

- A managed application cannot invoke an undeclared service operation.
- Exec/interpreter managed workflows cannot carry a service binding.
- Managed workflows cannot request exec startup without an explicit command.
- Valid managed application operations and all current templates remain valid.
- Retired local runtime profiles are rejected without conversion.
- English/Chinese specification and engineering evidence reflect actual checks.

## Evidence

See the [verification record](../../../evidence/verify/2026-10-23-workflow-review-validation.md).
