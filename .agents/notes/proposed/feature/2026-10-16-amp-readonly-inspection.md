# Decision: Preserve Amp configuration during inspection

Status: proposed

## Problem

Version and setup inspection wrote configuration and enabled allow-all; the remote verifier opened a server path on the controller and inferred server credentials from local environment variables.

## Decision

Make configuration inspection read-only, preserve existing settings and expose permission bypass only through an explicit request. Ship conservative image defaults, redact success/error output and stop owned process groups at the execution deadline. Version the changed contract as 1.2.0 and keep historical 1.1.0 provider evidence intact.

## API Design

`amp_execute` and its alias accept optional `dangerously_allow_all=false`. Setup adds `settings_exists`, returns false/default for absent settings and does not create or chmod files. The HTTP verifier uses the server's key-present boolean and never executes the model when disabled. Opt-in coding acceptance seeds an owned target project and requires source edits, downloaded artifacts, unchanged tests, independently executed isolated Python tests and held-out source checks; response text alone cannot pass. Responses remain buffered.

## Alternatives considered

Automatically writing settings from a check changes caller configuration. Using the controller's credentials or filesystem cannot establish remote state. Existing 1.1.0 evidence cannot validate changed 1.2.0 behavior.

## Dependencies

Pinned Amp CLI, the server SDK and an actual Amp credential for future model acceptance. The Express diagnostic uses short RPCs to poll a background installation after a long RPC stream failed; its owned sandbox contains and cleans up that job.

## Test Strategy

Exercise real subprocess deadlines/descendants, configuration byte/mode preservation, explicit permission argv, missing-key refusal, output privacy and remote-verifier negative cases. Run local HTTP checks and keyless real Express source-runtime checks with a clean, source-matched server wheel.

## Acceptance criteria

- Inspection never writes or changes settings permissions.
- Permission bypass is explicit; current image defaults do not enable it.
- Missing keys never launch device login; configured secrets are omitted from output.
- Model-disabled verification never invokes the agent, including remote keyed servers.
- Bilingual docs, catalog and historical evidence accurately distinguish the changed version.
- Image build/deploy and actual Amp coding remain open requirements.

The follow-up review adds real subprocess regressions against writable `unittest.py` and `sitecustomize.py` shadows, and protocol fixtures rejecting marker-only responses, modified tests and failing independent checks. Genuine product acceptance remains blocked until a compatible key is injected into the target.

## Evidence

[Verification](../../../evidence/verify/2026-10-16-amp-readonly-inspection.md), [issue #83](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/83), [PR #82](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/82).

[Independent completion review](../../../evidence/verify/2026-10-16-four-template-completion-review.md).

Completion cleanup follow-up: retain the Linux session leader unreaped until final owned-group KILL, drain stdout/stderr concurrently, and clean descendants after successful/nonzero completion as well as deadline expiry. Real redirected-descendant and TERM-ignoring-child regressions accompany the fix. [Verification](../../../evidence/verify/2026-10-16-amp-droid-gemini-owned-processes.md).

Image-gate follow-up: normalize the server SDK install to COPY plus a source-wheel conditional, preserving the61c43e0fallback archive pin. Public pinned source wheels can now be installed from the standalone template context without CI rewriting the SDK RUN instruction. [L1 gate preparation](../../../evidence/verify/2026-10-16-template-image-build-gate.md).
