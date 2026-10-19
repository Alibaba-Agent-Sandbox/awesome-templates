# Decision: Separate browser dependency installation stages
Status: proposed

## Problem

Actual generated Express browser build failed with RUN stream deadline_exceeded after306.777seconds. The combined pip, system dependency and Chromium download step failed. A later successful400-second step disproves a universal300-second execution cap; large-asset transport remains a measured constraint.

## Decision

Split the three installation phases into separate Docker RUN instructions, preserving Playwright1.58.0 and the full Chromium profile. Bump template2.0.0 to2.0.1. No command API changes.

## API Design

No runtime/SDK contract change; both Dockerfile and generated platform steps inherit the explicit build phases.

## Alternatives considered

Increasing overall readiness did not make the observed attempt succeed. Skipping Chromium or marking source-only execution passed would not satisfy browser acceptance. Keep the same full browser install and actual tests.

## Dependencies

PR121 step adapter exports exact build environment and records provenance. Tracking Issue22; real browser artifacts remain mandatory.

## Test Strategy

Static/spec/doc checks, exact generated phases; actual cloud build and CLI/SDK browse; external remote PNG and form/isolation suite; current-head CI actual L1 image.

## Acceptance criteria

Real build and full external browser behavior, independent owned cleanup, preserved historical failures, current-head CI and ordinary merge.

Follow-up real build-network execution exceeded300seconds, so the earlier stream deadline is not a universal per-RUN cap. Stage separation is retained; slow large-asset transport remains unresolved.
