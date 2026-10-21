# Decision: correct the Devin process diagnostic origin

Status: proposed

## Problem
Fresh review after Issue72 delivery found that the reused bounded process helper still named Cursor in timeout/overflow/pipe-cleanup errors and its private module name. Actual original native/API behavior passed, but diagnostic origin was misleading.

## Decision
Correct the copied helper labels to Devin, add a real authored-subprocess timeout regression and bump template1.0.1. Preserve1.0.0 receipts as history and requalify exact changed source before claiming current provider support.

## API Design
No parameter, original upstream version, permission or success-result change. Errors now correctly identify Devin; no raw output or new credential is exposed. Version1.0.1 records this diagnostic behavior correction.

## Alternatives considered
Leaving another vendor name makes operational debugging ambiguous. Reusing1.0.0 receipts for changed process bytes violates provenance, even though the fix is small. No broader runtime/process refactor is needed.

## Dependencies
Unchanged original Devin3000.11.92 and pinned SDK34e7e011c5569f77b7f605e65313be7498f6cf02. Vendor account remains unavailable; original no-account HTTP/SDK refusal is tested separately from model success. Refs https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/72.

## Test Strategy
Regression first invokes an authored fixed worker with an actual1second deadline and expects a Devin error, failing before the change. Rerun wrapper/controller/installer tests, strict/docs, exact-source native Express SDK/fullHTTP16/0/0 with independent cleanup, current receipt audit and image/latestCI/review/normalmerge. No original/generated code runs on operator.

## Acceptance criteria
Correct diagnostic labels, meaningful before/after regression, current1.0.1 receipts and bilingual claims, indexed evidence, required checks and actual normal merge. No vendor-authenticated/model claim or alteration of historical evidence.
