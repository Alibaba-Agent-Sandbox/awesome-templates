# Decision: Managed-session application templates

Status: proposed

## Problem

Business callers need a stable Gateway while the Agent harness executes in a
session-owned Sandbox. Existing spec5 only describes per-run ownership and the
local agents-cli template does not supply a durable managed application.
Issue: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/295.

## Decision

Add an independent closed spec6 profile without changing existing spec5 meaning.
Use a private managed bridge identity, one explicit guest startup/readiness and
operation-based local smoke. Keep generic runtime and cloud deployment code in
their owners. Add an agents-api template only with honest dependency, image,
Provider and model acceptance boundaries.

A private State binding can borrow an existing explicit FC VPC configuration;
network resources are never provisioned by this template. Optional bounded
certificate-only database CA input configures Server trust without weakening
DSN hostname verification or entering guest/build/plan/receipt payloads. CLI-owned Server image
builds have a separate unused-build cleanup command; builds that entered Apply
remain under app Destroy/Retire ownership, while borrowed images and retained
Sandbox build artifacts keep their distinct cleanup rules.

## API Design

The managed Gateway uses agent-sandbox-managed-agents/v1; the guest is separately
agent-sandbox-managed-bridge/v1. Per-session ownership, finite budgets, role-bound
service references, Server build/image selection and bounded typed verification
hooks form the author contract. Profile expansion is managed deployment, not a
general workflow language. Public callers do not receive guest or cloud credentials.

## Alternatives considered

Reusing server-core-agents would misidentify a new private receipt protocol.
Mutating spec5 would change unrelated templates. Copying the generic Gateway into
the template would duplicate ownership. A diagnostic command is not a managed
bridge or complete Agent acceptance.

## Dependencies

Shared runtime: https://github.com/Alibaba-Agent-Sandbox/python-sdk.
Deployment owner: https://github.com/Alibaba-Agent-Sandbox/agent-sandbox.
Catalog consumer: https://github.com/Alibaba-Agent-Sandbox/registry.
New package availability must be checked independently from source installation.

## Test Strategy

Behavior regressions cover valid/invalid version combinations, private protocol
identity, role injection, budgets, image/build exclusivity, hook restrictions,
source escape and actual local startup selection. Run owner specification and
catalog/document checks. Local/image/cloud/model acceptance and cleanup remain
separate required evidence; none follows from schema validity.

The coding smoke uses an intentionally defective, pre-existing CSV exercise,
unchanged original tests, decimal-valued data and two successive source edits. It
downloads the actual modified source and verifies independent CSV totals/shares.
A trusted engineering inspector may run between published turns and before close,
using owned Provider access for source/test hash checks and original/held-out tests
inside the Sandbox. Business calls remain Gateway-only, and generated source is
never executed in the host process. This closes an acceptance-design gap without
claiming the new image/model path has already run.

The branch integrates the independently published spec6 contract at
`31fe653c2940d8681b9549be3f570977152847a7` without changing schema bytes. Keep
its temporary complete-checker regression and independent importlib loader
coverage. The executable template runner replaces the contract-only unsupported
guard with strict preflight validation before preparation and the exact managed
module startup. It loads its own sibling validator by fixed file origin, so
standalone file loading and package imports both work without global path changes.
Source/candidate L0 remains distinct from public dependency availability.

The admission review found that attachments cannot target the seeded exercise's
nested input directory. Version0.1.2 keeps source/tests in the exercise directory
and uses the supported `/workspace/input/sales.csv` target in the upload and both
turn prompts. The real local service rejects the prior target and accepts the
corrected target without any Provider/model execution. The runtime's input-path
allowlist is preserved.

## Acceptance criteria

- Supported version selection is closed and existing spec5 inputs remain valid.
- The actual bridge starts during L0; named diagnostics cannot impersonate it.
- Manifest/recipe/catalog/user translations and new dependency versions agree.
- Required local, image, Provider/model and owned cleanup evidence exists.
- Current-head CI/review pass and the scoped PR is verified merged.
