# Decision: Conformant Gemini headless runtime with explicit coding acceptance

Status: proposed

## Problem

The legacy Gemini template used a Python base, image CMD, unpinned server fallback and unconditional yolo. It lacked spec-2 diagnostics, cwd/deadline controls, Chinese README and design. Its model smoke accepted a response marker without verifying work. Refs [Issue #30](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/30).

## Decision

Retain actual verified Gemini CLI 0.64.0. Migrate to Alibaba base, non-root user, generation 2 and pinned server archive/injected wheel. Add read-only setup/version commands, typed timeout/yolo and WORKSPACE-contained cwd. Default to upstream plan mode; yolo requires explicit consent in the command arguments. Redact secret environment values on successful and failed output; deadlines kill the owned process group without exposing prompt argv.

## API Design

`gemini(prompt: str, model: str="", cwd: str="", command_timeout: int=600, yolo: bool=False) -> str`; timeout range 1–1800 seconds. API key is Gemini-only and missing/whitespace refuses CLI launch. Return remains a string but contains buffered upstream JSON. `gemini_version() -> str`; `gemini_setup_check() -> dict` reports metadata, not config values. Version 2.0.0 documents explicit opt-in permissions as a compatibility change. HTTP authentication remains the server SDK's contract.

## Alternatives considered

Do not upgrade the upstream CLI without reason, invent a max-turns flag, silently substitute an OpenAI-compatible key, rewrite user auth settings, retain unconditional yolo, or treat a response marker as coding acceptance. Actual package metadata/help established Node >=20 and supported flags.

## Dependencies

Pinned npm package; server archive commit `35da216a300f1e2e84254a1cf4b4a7ea98681505` or deployment-injected wheel; Alibaba runtime base; genuine Gemini key/model availability. CLI/server/provider changes retain their own repository ownership. Catalog updates are coordinated separately in this repository.

## Test Strategy

Behavior regressions exercise read-only settings, actual installed binary diagnostics, missing-key no execution, approved flags/typed bounds, directory traversal/symlink rejection, both output paths' redaction and descendant deadline cleanup. Protocol regressions require target-side credential inspection and zero coding requests when forced off, and reject marker-only, changed tests and failed independent checks. L3 seeds failing source/tests through remote APIs, requires repaired existing source and new artifacts, preserves tests, executes independent and held-out target checks, then cleans its unique project.

## Acceptance criteria

- Checker and local server L0 pass with model execution explicitly skipped.
- Actual pinned CLI version/help and behavior regressions pass.
- English/Chinese CLI/SDK/POST, parameter/error/auth/deadline/development docs agree.
- L1 real image build and L2 external cloud CLI/SDK smoke remain required for provider acceptance.
- L3 passes only with a compatible target key, real edits/artifacts and independent tests. Missing key is blocked, never accepted.
- Cross-review, owning-repository PR/CI and verified merge remain required for delivery.

## Evidence

[Verification](../../../evidence/verify/2026-10-16-gemini-runtime.md). No L1/L2/L3 pass is claimed. Historical image-build records describe earlier source and remain unchanged.

Subsequent verifier hardening: [isolated coding verifiers](2026-10-16-isolated-coding-verifiers.md) and [new point-in-time evidence](../../../evidence/verify/2026-10-16-gemini-qwen-isolated-verifier.md).

Completion cleanup follow-up: retain the Linux session leader unreaped until final owned-group KILL, drain stdout/stderr concurrently, and clean descendants after successful/nonzero completion as well as deadline expiry. Real redirected-descendant and TERM-ignoring-child regressions accompany the fix. [Verification](../../../evidence/verify/2026-10-16-amp-droid-gemini-owned-processes.md).
