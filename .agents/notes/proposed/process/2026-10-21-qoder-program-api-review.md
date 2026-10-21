# Decision: verify Qoder native API without vendor credentials

Status: proposed

## Problem
Issue24 has deployed template1.1.1 evidence but no available vendor PAT. The fresh request requires program/API testing even when authentication cannot succeed.

## Decision
Retest unchanged Qoder on Express and call its actual native CLI through SDK qoder using an explicitly invalid fixed synthetic PAT. Require a native authentication refusal; timeout/missing-binary/unknown errors fail. Record model/account success as NOT_RUN. Retain all prior receipts and experimental status.

## API Design
N/A — existing qoder/version/setup/local Python compatibility signatures are unchanged.

## Alternatives considered
Installation/version alone does not test the native API error path. Sending Express or compatible-model credentials to Qoder would violate their scope. A fake successful model endpoint would not verify vendor authentication.

## Dependencies
Original pinned Qoder1.1.72, unchanged template1.1.1, exact native step source/controller, current SDK and Express. Synthetic invalid PAT is an authored negative fixture, not a real secret.

## Test Strategy
Existing33protocol/process/controller tests; full real native steps/SDK create/CLI+SDK smoke/HTTP9PASS1authSKIP; actual original native API authentication refusal; independently confirmed secondary and outer cleanup; prior exact-main actual image/full local CI; current strict/docs/records/CI/review.

## Acceptance criteria
Native program/API path is executed and auth-dependent omission remains explicit. Every Issue24 non-credential criterion is delivered; no full authenticated coding/model claim. Preserve runtime/catalog status and original evidence, complete latest checks/review and normal pinned merge.
