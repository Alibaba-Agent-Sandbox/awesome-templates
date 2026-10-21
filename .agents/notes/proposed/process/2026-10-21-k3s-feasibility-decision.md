# Decision: Publish K3s feasibility evidence without an unqualified template

Status: proposed

## Problem

Issue42 explicitly asks to decide/document with evidence and implement only on a provider where K3s really runs; it expects Express may not support privileged nesting. A narrower non-root agentless original API experiment still failed actual readiness/validation and cannot be published as a working template.

## Decision

Retain seven actual canonical Express attempts, immutable original source/asset provenance, component checks, failures and independently verified cleanup. Reject the unqualified prototype for the current catalog and remove its source template, catalog row, shared asset/materializer/receipt branches and image/HTTP CI changes. Preserve reviewed experimental commits and the rejected engineering note. Add bilingual product-specific feasibility and explicit prerequisites for reopening implementation. Restore all46 existing source templates and shared runtime files to reviewed main unchanged.

## API Design

No new template, named command, feature gate or provider qualification is exported. K3s documentation describes a decision, not an installable template or a successful server/worker cluster. Actual original version/help and image preparation do not imply API readiness. No synthetic advertised endpoint, privilege escalation, patched original binary or weakened native acceptance is used.

## Alternatives considered

Publishing the failing agentless prototype would misrepresent useful behavior. An invented advertised address or skipped readiness/cleanup would not meet the contract. Full privileged nesting on an unavailable target remains untested. A later qualified provider/profile can reopen implementation with its own exact source, real API/workload and cleanup evidence.

## Dependencies

https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/42. Original source356c025475bbefaa09cf0d7e48e8e2adbbde57db and original binary SHA25692b94582eb7b34a8cf532e6006842b9ed215a6783cf56a3dd6271fd35243b2c0. Experiment0e28a50 remains in public commit history; this final change depends on no new SDK/provider contract.

## Test Strategy

Verify all seven native failures and owned cleanup receipts, exact original provenance and component scope. Re-run mandatory57spec tests,46source strict checks, managed catalog, bilingual document and engineering-record links. Ensure the final diff contains no installable K3s source or shared runtime changes. Required latest-head CI/review/normal merge and actual Issue closure remain delivery gates.

## Acceptance criteria

Publish an honest evidence-backed decision matching Issue42's explicit alternative; keep failed attempts distinct from passes; preserve46 existing qualified sources unchanged; complete current-head CI and review before merging. No complete K3s runtime or cluster success is claimed.

## Evidence

[Final seven-run inventory](../../../evidence/verify/2026-10-21-k3s-final-feasibility.json), [original experiment verification](../../../evidence/verify/2026-10-21-k3s-agentless-validation.md), [rejected prototype](../../rejected/2026-10-21-k3s-agentless-validation.md).

[Final static verification](../../../evidence/verify/2026-10-21-k3s-final-decision-checks.md).
