# Decision: Index recent changes to application profiles, template recipes and acceptance
Status: proposed

## Problem

Recent implementation, user-experience changes and delivery status are spread across
owner records, pull requests and workspace reports. The user requested that recent
changes be retained under each owning repository's `.agents/` and pushed.

## Decision

Keep this dated index in awesome-templates; link existing canonical decisions and immutable
verification instead of copying their reports or rewriting historical acceptance.
This index adds no product behavior and does not change any older ADR's lifecycle.

### Owner changes and canonical records

The candidate owns the shared pure Python/JavaScript application-profile defaults and strict normalization fixtures, compacts agents-api to 0.1.5, and migrates current guides/controllers to the unified source CLI. Explicit conflicting fields remain invalid. Historical source identities and receipts remain historical. The previously merged agents-api 0.1.4 workflow is distinct from this candidate.

- [Shared fixed application profile defaults](../../../notes/proposed/process/2026-11-10-application-profile-defaults.md).
- [Producer profile verification](../../../evidence/verify/2026-11-10-application-profile-defaults.md).
- [Current CLI guides and executable controllers](../../../notes/proposed/process/2026-11-10-current-cli-workflows.md).
- [Controller and image-smoke follow-ups](../../../evidence/verify/2026-11-10-current-cli-workflows.md).
- [Previously delivered 0.1.4 core workflow](../../../evidence/verify/2026-11-06-managed-agents-cli0510-prerequisite.md).

### Mainline and candidate boundary

- Mainline observed: `e94ab308a74715982bb059b142518f7d6070c1c2`.
- Candidate/source observed before this records commit: `957cd1e3f52f7002cfe24a103653b855a7dd9747`.
- [awesome-templates PR #305](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/305), OPEN and Draft at the recorded query; not merged.
- The unified source CLI is different from published CLI 0.5.10. This task does
  not issue npm/PyPI releases, deploy sites or certify changed templates.

Recent mainline changes, inspected from the refreshed Git history:

| Date | Commit | Change |
| --- | --- | --- |
| 2026-11-07 | [e94ab308a747](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/commit/e94ab308a74715982bb059b142518f7d6070c1c2) | feat: add single-endpoint Agents API sandbox template (#296) |
| 2026-11-06 | [31fe653c2940](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/commit/31fe653c2940d8681b9549be3f570977152847a7) | feat: publish managed-session manifest contract (#299) |

### Remaining delivery limits

Fresh runtime/cloud acceptance for changed source identities remains incomplete. The queried current head has failing e2e and Template images (L1) workflow conclusions. The existing LibreOffice package-resolution blocker is tracked in Issue #304; this records task neither diagnoses every failed job nor weakens pins or checks. Architecture documentation PR #301 is independent and remains open according to its separately queried status.

## API Design

N/A — this decision does not involve API changes. Existing runtime, credential,
source identity and resource ownership contracts remain with their original owners.

## Alternatives considered

- A workspace-only summary cannot travel with an independent checkout.
- Copying all cross-repository reports duplicates authority and may expose private logs.
- Marking all proposed records implemented would confuse source work with accepted delivery.
- Combining unrelated local changes or permission-only differences in this commit
  would conceal the actual records scope.

## Dependencies

Existing owner records and GitHub PR/commit state. Coordinated implementation is
tracked in [CLI Issue #244](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues/244).
Each repository retains its own branch, record, verification and push.

## Test Strategy

Check the new record structure, relative links, pinned Git source revisions and
scoped diff; run the owner's applicable documentation/health checks. Query PR/CI
state separately from local checks. Do not run cloud tests solely to validate prose.

## Acceptance criteria

- Recent owner work is reachable from `.agents/README.md` with dated source references.
- Merged, Draft, failed, unrun and planned work remain distinguishable.
- Existing historical evidence and unrelated work remain intact.
- Documentation checks and remaining gates are recorded; scoped commits are pushed
  to task branches and remote branch hashes are independently compared.

## Evidence

- [Records verification](../../../evidence/verify/2026-11-10-recent-change-index.md).
