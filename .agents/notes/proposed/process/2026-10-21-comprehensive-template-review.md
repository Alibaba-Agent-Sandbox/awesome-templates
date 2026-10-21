# Decision: audit every template with distinct execution scopes

Status: proposed

## Problem
The user requested a fresh review and tests for every template, including program/API checks when vendor credentials are absent. Prior completed Issues and installation results alone cannot establish this.

## Decision
Run every existing local HTTP target and every installable template regression suite; independently inspect exact-main hosted CI and immutable current runtime/controller receipts. Publish a per-template matrix with failed prerequisite cases and skips intact. Keep candidate native/model runs in their owning template PR.

## API Design
N/A — this decision does not involve API changes.

## Alternatives considered
Treating missing credentials as no tests, or relabelling source-only/mocked/installation results as original-native/model acceptance, would hide gaps. Replacing failed local cases with hosted passes would also erase their execution scope.

## Dependencies
The exact main revision, existing44 template suites, declared SDK/dependencies and completed hosted checks. Current Express receipts bind each runtime input and controller. No new production dependency.

## Test Strategy
57spec tests, strict catalog,200Markdown local links;44 isolated regression processes;45HTTP targets including skeleton;44/44current step/controller evidence audits;51 completed exact-main hosted checks and actual45/45hosted HTTP summary. Preserve initial operator failures and the dependency-corrected OCR rerun separately.

## Acceptance criteria
Every existing installable template appears in the matrix; failures/skips/authentication limits remain explicit; no missing roadmap template is counted as tested. Latest documentation/record CI and scoped review/normal merge required. This record does not close the remaining12 original Issues.
