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
catalog/document checks. Local/image/cloud/model checks and cleanup remain distinct evidence;
none follows from schema validity. The current ordinary public CLI0.5.10 and
SDK0.4.0a7 recipe0.1.4 deployment reached ready and its own Gateway-only smoke
completed two actual Qwen turns, downloaded results, and closed/deleted the Session.

The coding smoke uses an intentionally defective, pre-existing CSV exercise,
unchanged original tests, decimal-valued data and two successive source edits. It
downloads the actual modified source and verifies independent CSV totals/shares.
A trusted engineering inspector may run between published turns and before close,
using owned Provider access for source/test hash checks and original/held-out tests
inside the Sandbox. Business calls remain Gateway-only, and generated source is
never executed in the host process. The stronger historical inspector results retain their original source/recipe identity;
the current core delivery uses the template Gateway-only two-turn check.

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

The initial public dependency transition pinned both images to published
PyPI0.4.0a7 and used npm CLI0.5.9 with Node20+ and a private `.abx/venv` containing
httpx0.28.1. Its dated source and public0.1.2/0.1.3 results remain separate evidence.
After formal npm CLI0.5.10 publication and independent fresh installation,
version0.1.4 raises the documented deployment prerequisite to0.5.10. The revised
CLI waits within the existing bounded health budget until the exact revision
is confirmed; unrelated or malformed HTTP200 bodies never establish readiness.
This dependency change leaves both a7 Dockerfiles, smoke assertions, API and
execution limits unchanged. Keep Beta and the documented capability boundaries. The user narrowed final
delivery to the unified Server Gateway, Agent execution inside an owned Sandbox,
related real two-turn file workflow, practical article and owned resource release.
Do not make a wider API/upgrade/qualification matrix or new cross-repository
publication a prerequisite for this scoped template delivery.

## Acceptance criteria

- Supported version selection is closed and existing spec5 inputs remain valid.
- The actual bridge starts during L0; named diagnostics cannot impersonate it.
- Manifest/recipe/catalog/user translations and new dependency versions agree.
- The exact public recipe normally deploys and completes its two actual Agent file turns, downloads, Close/Delete and owned cleanup.
- Broader historical API/SSE/cancel/upgrade results keep their exact dated scope and do not become new0.1.4 claims.
- Current-head CI/review pass and the scoped PR is verified merged.


The public Qwen API, stream and active-cancel paths pass, but a later public
Codex update stops at its candidate business hook. Its exact cause remains
unknown: the original smoke catch discarded its controlled check label, and the
deployer removed the temporary hook result. Version0.1.3 adds a bounded local
phase/check report before HTTP admission, with per-attempt append-only files
and an atomic latest snapshot outside that temporary directory. It records only
finite codes, numeric HTTP status, terminal enums and known-cleanup booleans.
Main business assertions, model prompts, execution budgets and the existing
hook result protocol stay unchanged. New local evidence is in
[the report verification](../../../evidence/verify/2026-11-06-managed-agents-smoke-reports.md);
the failed public update is not retroactively reclassified, and the wider historical cloud Codex/upgrade evidence remains separate from the current core acceptance.
