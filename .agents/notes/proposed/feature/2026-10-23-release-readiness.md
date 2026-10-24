# Decision: Align release build sources and pin Qwen runtime

Status: proposed

## Problem

Thirteen catalog templates and the skeleton installed a different server archive by default than the source used to build CI wheels. Qwen used a moving NodeSource setup script. A pinned manifest alone did not make these two build routes equivalent.

## Decision

Align those fallback archives with the existing common server source e2cb27e24fde0a67112f82b8d44af463445a5d1a, including python-hello's explicit portable profile. Keep existing per-template server-sdk.commit overrides. Validate the selected CI pin against declared default Dockerfile archives even without an override file. Install Qwen's Node24.16.0 from fixed official x64/arm64 archives with upstream SHA256 verification, following the existing Kimi recipe.

Affected templates: amp, apply-patch, codex, deepseek-harness, hermes-agent, kimi-code, node-web, openclaw, opencode, polyglot-toolchain, python-hello, qoder, qwen-code; also _skeleton. Each dependency change receives a patch contract version and bilingual README/design note. Historical acceptance remains immutable.

## API Design

No named-command or workflow API changes. A different fallback now fails preflight instead of receiving a CI receipt for a different source. Users with deliberate per-template sources retain the explicit server-sdk.commit mechanism. New image/workflow acceptance is required for changed build identities.

## Alternatives considered

Keeping two different source routes and adding duplicate CI matrices retains needless ambiguity. Updating every template to the newest SDK would broaden the dependency change. A registry version service is unrelated and unnecessary.

## Dependencies

The existing paired public Python server source and official Node release archives. Current main already uses workflow schema4; this patch does not reinstate old capability gates or rewrite those contracts.

## Test Strategy

Run spec and catalog checks, mismatch rejection regressions, image proof/workflow guards, Qwen behavioral regressions and actual pinned Node/Qwen version smoke. Image/native/model checks remain separate gates and require available Docker/backend infrastructure.

## Acceptance criteria

- Default archives and injected source pins agree; mismatch is rejected.
- Qwen installs the exact checksum-verified Node release and pinned CLI.
- Local regressions pass; changed image/workflow acceptance is explicitly pending.
- No historical receipt is rewritten or promoted to current-source evidence.

## Evidence

[Verification](../../../evidence/verify/2026-10-23-release-readiness.md).
