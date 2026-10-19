# Decision: Exact-source CI image acceptance
Status: proposed

## Problem

Actual heavy-template step builds timed out while some large asset transfers
measured385–398 seconds for8MiB. CI image builds succeed, but do not establish
Express runtime acceptance. The controller host has no Docker daemon.

## Decision

Use explicit keyless public CI archive export, inspect exact source/image bytes,
transfer to a nonce-owned private ACR repository with RAM-only temporary auth,
and invoke real native template create with the nonce-owned review tag. Live digest readbacks before registration and after runtime bind that tag to checked bytes. Preserve step
failures and clearly record image mode. Publish acceptance only after independent
sandbox/template and registry cleanup.

## API Design

express_e2e adds explicit --build image, --image-ref and --image-proof, with
source/proof checks before cloud mutation. run_ci_image_e2e composes verified
artifact transfer, canonical CLI/SDK smoke and external HTTP; models remain
NOT_RUN. ci_image_archive handles archive inspection and scoped recovery journals.

## Alternatives considered

A fake Docker wrapper would misrepresent execution. Public object cache was denied
by existing policy and independently cleaned. Changing account policy or passing
cloud/model secrets to CI is unnecessary. Step builds remain preferred where
verified feasible; image mode has a distinct receipt.

## Dependencies

Tracking Issue119, native CLI0.3.0, paired SDK and pinned image server e2cb27e,
existing image-build workflow, official crane0.22.1 and ACR ROA API. Linux memfd
is required; mutable references, source drift and unsigned context changes fail.

## Test Strategy

Regress actual layer selection/deletions/non-root checks, source mismatch,
RAM-only auth inheritance/cleanup, atomic private journals and failure publication.
Then exercise genuine completed CI artifacts, private transfer, native registration,
full HTTP behavior and independently confirmed owned cleanup.

## Acceptance criteria

No secret-bearing files/CI uploads; no unverified provider badges; no PASS receipt
before owned resource absence; immutable provenance and failures preserved; current
head CI and ordinary merge. Every template retains its own required product/model
gates.

Actual digest-form registration attempted to pull latest and failed on2026-10-19. This provider path therefore uses the nonce-owned tag plus before/after digest readback; no provider digest-reference support or registry tag immutability is claimed.
