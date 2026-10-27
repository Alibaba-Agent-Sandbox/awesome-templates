# Decision: verify and retry the immutable Hermes source archive

Status: proposed

## Problem
An actual OpenSandbox build of Hermes1.2.0 aborts before creation when the fixed
codeload source request returns HTTP429. Curl's pipe feeds a partial archive to
tar; the CLI correctly retains an image intent with no ID for reconciliation.

## Decision
Download with bounded retry/backoff for transient429/5xx/network failures, then
verify exact size/SHA before atomic output and extraction. Preserve the fixed
upstream commit, native Python/uv versions, frozen lock and install stamp. The
canonical cached build uses the same verifier and retains the historical literal
recipe. Template1.2.1; source metadata is shipped with the standalone template.

## API Design
No named command/schema/model changes. Four attempts/120-second default budget,
verified HTTPS, Retry-After support, size ceiling and no partial destination.
No GitHub or platform credentials injected into image builds. Archive hash is
controller-measured, not claimed to be an upstream-published checksum.

## Alternatives considered
Retrying an uncertain operation without absence checks or extracting an incomplete
response is incorrect. Removing integrity checks, changing the upstream commit,
unbounded retries or borrowing credentials would weaken the build contract.

## Dependencies
Refs https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/284 and
https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/244.
Source83225459 bytes, SHA256fbd55e510b49592635429aa451a7c2b9fb4061cddbbab09f52504226f4338fcf.
The original current-source failure is retained. Independent exact local tag and
remote404, no sandbox entries/active build/workload establishes cleanup; no new
business/model calls were used for that supplement.

## Test Strategy
Actual loopback HTTP429→200, bounded repeated429,403 non-retry, corrupt checksum,
atomic destination preservation, cleartext rejection and cached integrity checks.
Three archive files match Git blob hashes at the unchanged fixed commit. Related
Hermes/canonical suites110 PASS; legacy/current cached source compatibility PASS.
Spec39, all-template checker and224-document links pass. Fresh current Express/
OpenSandbox native/method/model/documentation/business/owned-cleanup still required.

## Acceptance criteria
Final-head CI/review, fresh full dual-provider use, exact owned cleanup, source and
current-source Registry publication. No build-only provider or full50 pass claim.
