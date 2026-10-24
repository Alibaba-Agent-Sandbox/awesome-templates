# Decision: Reproducible public developer journey documentation

Status: proposed

## Problem
The public Registry python-hello journey has a stale server-source pin and no concise current no-Docker path; historical CLI instructions obscure the current entry.

## Decision
Correct source READMEs and bilingual steps instructions. Use the existing preparation tool, preserve all runtime inputs and historical receipts, and show exact ownership-based cleanup.

## API Design
N/A — documentation only; no runtime or package version changes.

## Alternatives considered
Do not add a registry service, silently translate arbitrary Dockerfiles, or rewrite runtime APIs to make documentation examples appear universal.

## Dependencies
- Issue: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/201
- Related source owner: https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues/92
- Registry republishes these source documents; generated output is not hand-edited.

## Test Strategy
Run owner documentation/record checks and required CI. Verify published wheel imports and the existing preparation command where relevant. After source publication, read Registry pages back and repeat the documented real-cloud journey with exact-ID cleanup.

## Acceptance criteria
Both language versions are accurate; current documented commands run against published tools; source changes are visible publicly; the affected experiment passes and owned resources are independently absent after cleanup.

## Evidence
[Verification](../../../evidence/verify/2026-10-24-developer-journey-docs.md).
