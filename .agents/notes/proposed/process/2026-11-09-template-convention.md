# Decision: Useful template design and evidence-based catalog evaluation

Status: proposed

## Problem

Installed tools, maintenance labels and a successful build do not tell users
whether a template delivers a useful task, exposes meaningful customization or
requires resources outside its Sandbox. The request asks for a development
convention, AI assessment of every template and a truthful distinction between
Sandbox and application delivery. It also asks whether the previously delivered
managed Agents template actually succeeded and needs further releases.

## Decision

Publish a bilingual contributor convention and AI review procedure. Assess the
fixed current catalog semantically, using source citations and five dimension
scores without a universal total. Keep performance unassessed unless measured,
and keep AI judgments separate from provider/model acceptance and Beta status.
Describe source/provider-managed origin separately from delivery type. Preserve
foundation, native-protocol and benchmark use cases rather than forcing every
entry into a business application.

Separate template-owned executable facts from Registry presentation and derived
reviews. No new manifest syntax, Registry UI, runtime behavior or release is part
of this documentation/assessment change. Use independent reviewers for design,
catalog inventory and prior delivery status, partition the initial row reviews,
then challenge selected classifications/scores and reconcile material differences.
Record actual review coverage rather than claiming every row was reviewed twice.

## API Design

N/A — no executable API changes. Existing typed named commands are already HTTP
operations; they must not be confused with arbitrary process execution. Future
Registry ingestion requires a separately reviewed consumer contract. The JSON
assessment is derived engineering evidence, not accepted manifest configuration.

## Alternatives considered

Reject requiring redundant REST wrappers for IDE/CDP/foundation templates,
equating API presence with better performance, scoring from keyword counts,
automatically promoting Beta templates, or adding speculative runtime fields.
Do not repeat the cloud/model matrix or provision databases for a source review.
Do not reopen old generic application drafts to invalidate the narrower managed
Agents delivery. The merged final recipe demonstrates the recorded core workflow,
not complete API/model/upgrade/performance coverage.

## Dependencies

Existing specification, documentation/project standards and qualification rules.
Prior managed template delivery: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/296
and article: https://github.com/Alibaba-Agent-Sandbox/blogs/pull/33.
The application-status audit uses fresh remote metadata and immutable final
verification, without a new cloud inventory or resource creation.

## Test Strategy

Check documentation and engineering links, language parity, scoped diff, complete
catalog coverage, unique identity, score bounds, fixed-revision source citations
and file digests. Run the existing spec tools and all-template checker as broad
compatibility checks. Current-head remote CI remains a separate required gate.
Record static scope, challenges, corrections and performance unknowns explicitly.

## Acceptance criteria

Both contributor languages and repository navigation link the convention and AI
procedure. All catalog records at the fixed revision have delivery/origin,
scenario/interface/customization/resources, five justified scores, source links,
strengths, gaps and an action. Reports preserve exact unit labels and unknown
minima/usage, distinguish the application's Guest from its full footprint, and
do not change runtime/qualification. Required local checks and latest-head CI
pass; verify actual PR merge. No cloud resource is needed for this task.

## Evidence

[Verification](../../../evidence/verify/2026-11-09-template-convention.md)
and its linked complete assessment preserve execution scope and limitations.
