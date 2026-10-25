# Published template runtime and current acceptance paths

Status: proposed

## Problem

All 46 source templates and the skeleton retained injected-wheel/Git-archive server fallbacks despite a published client/server distribution. Old image CI asserted server 0.3.0, duplicate cloud paths checked obsolete API snapshots, and batch retries could skip new work based on historical PASS. Source commit metadata could be mistaken for the actually installed guest server.

## Decision

Install published `agent-sandbox-server==0.4.0a2` directly in each Dockerfile and increment each changed template patch. Remove archive/wheel fallback, eight opt-in files and their helper. Preserve keyless L1 and image export; use the existing public-template-launch runner for full provider-resolved application acceptance. Retire duplicate historical OpenSandbox/canonical cloud execution without removing authorization, export or controller coverage. Selected image batch entries always execute. Prepared-image acceptance always includes external HTTP at the public entry point.

## API Design

Source recipes declare one exact published package. Actual image and guest acceptance read back the installed version and compare it to that declaration. Current image proofs use `server_package_version`, rather than implying a Git source pin proves installed bytes. Host source-mode client testing does not certify a guest server source candidate. Provider image/registration ownership remains unchanged. Native prepare/build capability is retained; remaining step-consumer lifecycle migration is a separate dependent change.

## Alternatives considered

Keeping a compatibility fallback would retain unneeded pre-release interfaces. Adding another server-version registry, image verifier or launch mode duplicates the Dockerfile and current public acceptance runner. Historical receipts remain immutable instead of being relabeled for a new runtime.

## Dependencies

Published Python client/server 0.4.0a2 and current CLI contracts. Follow https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/221. Prepared-image lifecycle changes depend on https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/220; its consumer files were adapted without discarding owned-resource cleanup. Public CLI version pins change only after actual availability is independently confirmed.

## Test Strategy

Behavior regressions cover declared/actual package identity, missing/conflicting pins, immutable archive ownership/content, real Docker context preparation, full HTTP selection, read-only cloud authorization, registry deletion uncertainty, source/gateway URL handling and cleanup. Run spec/catalog/document gates and all applicable CI. Real image builds and new two-provider matrices are required; local mocks cannot certify a new public runtime.

## Acceptance criteria

- All 47 recipes directly pin published server 0.4.0a2 and receive patch versions.
- Focused behavior/spec/catalog/document checks and latest-head applicable CI pass.
- Retained L1/export and public acceptance execute with current dependencies and actual installed-version assertions.
- Genuine new candidate/cloud and fresh public-source runs retain failures, skips and independent cleanup; no historical PASS certifies new pins.
