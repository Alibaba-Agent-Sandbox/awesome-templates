# Decision: Complete template guidance synchronization

Status: proposed

## Problem

Unified command changes had landed, but some current examples, contributor text and cross-repository consumers still advertised retired entry points. The user requested complete implementation of the affected ecosystem synchronization.

## Decision

Audit all catalog entries and source/managed documentation. Correct root discovery, issue reproduction, skeleton and recipe comments, current controller documentation and Amp/Codex controller instructions. Dated acceptance evidence remains unchanged; no runtime qualification is inferred from prose or comment updates.

## API Design

No execution API or resource lifecycle change. Command examples follow the current CLI contract.

## Alternatives considered

Blind text replacement was rejected: historical runs and version-pinned cases must remain truthful. Rebuilding every template or repeating cloud matrices for documentation would not validate these text changes. Generated consumers must be refreshed from their actual source rather than hand-patched.

## Dependencies

Current CLI contract: https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/pull/247. Template producer: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/305. Registry and website consume the reviewed source commits after local validation.

## Test Strategy

Run owner document/link/record checks and relevant actual command or catalog checks. Verify generated consumer snapshots through their normal generators and local site builds. Record missing prerequisites and remote authentication failures separately.

## Acceptance criteria

Current user instructions resolve to supported commands; every catalog template is checked; historical commands have an explicit version/research boundary. Bilingual pages and generated consumers agree. No secrets, acceptance results or release claims are fabricated.

## Evidence

[Verification](../../../evidence/verify/2026-11-12-ecosystem-guidance-sync.md).

## Managed serving-template follow-up

The user requested the full agents-api setup, not only replacement of deployment
verbs. Acquire just the editable project through template init by catalog name,
retain host Python/httpx because afterReady runs the real Gateway business task,
and retain private binding references. Venv creates .abx without a redundant
mkdir. README links to repository-wide guides are absolute so extraction does
not break them. Label the Python example as the actual HTTP client; spec/checker
requirements and bilingual regressions distinguish this from a dedicated SDK.
The article's current deploy/status/update/delete instructions are refreshed
while its original 0.1.4 business results retain explicit version provenance.
No new CLI, runtime, dependency or deployment abstraction is introduced.
