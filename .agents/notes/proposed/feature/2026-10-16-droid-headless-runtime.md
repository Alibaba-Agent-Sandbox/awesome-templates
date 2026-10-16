# Decision: Conformant, bounded Factory Droid headless runtime

Status: proposed

## Problem

The existing Droid template used a non-platform base, unpinned server installation, root runtime, legacy template metadata and `/app` ahead of `WORKSPACE`. Its wrapper returned unsanitized upstream output and did not clean up descendant processes at its deadline. Its model acceptance checked a text marker without proving a code change or independently tested artifacts.

## Decision

Use the Alibaba platform image, exact `@factory/cli@0.241.1`, pinned server SDK archive fallback, generation 2 startup/readiness and non-root `user`. Preserve `droid` and expose model-free version/setup checks. Execute argv directly, honor WORKSPACE, constrain cwd after symlink resolution, require the Factory key before spawning, redact configured secrets in success/error output and enforce a 1–600-second deadline with owned process-group cleanup.

Replace marker-only L3 with a target-host coding fixture: reproduce a source defect, ask Droid to modify existing code and create artifacts, retrieve those artifacts through the remote file API, preserve test content, and independently rerun fixed and held-out tests. Never infer the remote key or CLI from the controller environment.

## API Design

`droid(prompt, auto="low", cwd="", command_timeout=300) -> str`; no shell interpolation. Empty auto retains read-only behavior; low/medium/high use exact upstream flags. New `droid_version() -> str` and `droid_setup_check() -> dict` require no model call. Range/value errors and execution failures follow the existing server contract. `command_timeout` differs from the client's HTTP `timeout`.

Compatibility: the project root changes from `/app` to `/home/user/app`; callers can set an existing WORKSPACE. Default autonomy becomes explicit low for project edits; callers retain the old read-only behavior with `auto=""`. No unsafe permission-bypass flag is exposed.

## Alternatives considered

- Keep the Python slim base: rejected because this CLI has no hard dependency preventing the required Alibaba base.
- Follow the latest Factory release: rejected; exact installed 0.241.1 and its flags were verified before implementation.
- Accept a response marker or allow a missing CLI to skip L0: rejected because neither verifies the delivered product.
- Pass prompts as shell strings: rejected because argv is sufficient and avoids shell interpretation.

## Dependencies

[Existing Droid issue #19](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/19), [official Droid Exec docs](https://docs.factory.com/droid-exec/overview), npm's exact release metadata, and the server SDK archive pin in [Dockerfile](../../../../droid/Dockerfile). The integrator must add the pinned Droid install and regressions to shared CI, and reconcile the catalog as experimental until required acceptance exists.

## Test Strategy

Real subprocess regressions cover privacy on success/nonzero exit, bounded descendant cleanup and literal argv. Protocol regressions reject controller-only credentials and marker-only responses. Independent held-out checks load the exact source file by absolute path under isolated Python, and real subprocess regressions reject writable standard-library/startup shadows while preserving passing correct-code scenarios. L0 starts the real server with the exact installed CLI and no model keys. Required L3 without a target Factory key must exit nonzero. L1/L2 require Docker and cloud prerequisites; those gates remain unmet in this environment.

## Acceptance criteria

- Template checker passes and English/Chinese usage documents match the runtime API.
- Meaningful regressions and real no-key HTTP L0 pass.
- Missing Factory key blocks required L3 without interactive login.
- L1/L2 and real-key L3 pass before provider/product acceptance is claimed; retain empty tested_on and no Verified provider until then.
- Cross-review, scoped commit and repository PR occur through normal gates; local implementation alone does not establish merge state.

## Evidence

[Verification record](../../../evidence/verify/2026-10-16-droid-headless-runtime.md).

Cross-review follow-up: [target-key authority and disabled-model verification](../../../evidence/verify/2026-10-16-qwen-droid-verifier-cross-review.md).

[Independent completion review](../../../evidence/verify/2026-10-16-four-template-completion-review.md).

Completion cleanup follow-up: retain the Linux session leader unreaped until final owned-group KILL, drain stdout/stderr concurrently, and clean descendants after successful/nonzero completion as well as deadline expiry. Real redirected-descendant and TERM-ignoring-child regressions accompany the fix. [Verification](../../../evidence/verify/2026-10-16-amp-droid-gemini-owned-processes.md).

Actual-image follow-up: the first remote L1build exposed a native optional-package mirror miss and upstream fallback self-link. Install the same pinned Droid release from the official npm registry with optional packages explicitly included; preserve the actual version assertion and await the new image run. [CI evidence](../../../evidence/verify/2026-10-16-image-build-first-ci.md).
