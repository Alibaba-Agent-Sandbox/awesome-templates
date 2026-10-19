# Engineering records: awesome-templates

This repository owns template source, specification, catalog and acceptance records.
Read [CONTRIBUTING.md](../CONTRIBUTING.md) and [the specification](../docs/template-spec.md).
New engineering records use English and stay in this repository.

- [Kimi Code runtime](notes/proposed/feature/2026-10-19-kimi-code.md)
  · [verification](evidence/verify/2026-10-19-kimi-code.md)

- [Contributor standards and platform steps](notes/proposed/process/2026-10-19-standards-and-platform-steps.md)
  · [verification](evidence/verify/2026-10-19-standards-and-platform-steps.md)
  · [actual platform limits and reruns](evidence/verify/2026-10-19-step-platform-limits.md)
  · [RUN environment verification](evidence/verify/2026-10-19-step-build-environment.md)
- [Provider-owned preparation](notes/proposed/process/2026-10-19-provider-preparation.md)
  · [verification](evidence/verify/2026-10-19-provider-preparation.md)

## Layout and lifecycle

- `notes/proposed/<architecture|feature|process>/YYYY-MM-DD-<slug>.md`: pending decisions.
- `notes/implemented/<category>/...`: accepted decisions reflected in code.
- `notes/rejected/` and `notes/superseded/`: flat historical decisions.
- `evidence/verify/YYYY-MM-DD-<slug>.md`: point-in-time validation summaries.

Use the seven ADR sections: Problem, Decision, API Design, Alternatives considered,
Dependencies, Test Strategy, Acceptance criteria. Status matches its directory;
local implementation alone does not establish an accepted or merged decision.

Record exact tested scope/revision, commands and outcomes, real versus synthetic
backends, missing gates and owned-resource cleanup. Use PASS, PARTIAL, BLOCKED or FAIL.
Keep per-template provider evidence in its established location and link to it.
Preserve historical evidence; new runs receive distinct filenames. Do not store
credentials, private prompts or unsanitized logs. Cross-repository links are absolute.

## Current review

- [Node Web HTTP output protocol](notes/proposed/process/2026-10-16-node-web-http-output.md)
- [Node Web protocol verification](evidence/verify/2026-10-16-node-web-http-output.md)
- [Catalog completion decision](notes/proposed/feature/2026-10-16-catalog-completion-review.md)
- [Verification](evidence/verify/2026-10-16-catalog-completion-review.md)
- [Image-build gate](notes/proposed/process/2026-10-16-template-image-build-gate.md)
- [Image-build preparation evidence](evidence/verify/2026-10-16-template-image-build-gate.md)

- [Codex existing-source acceptance](notes/proposed/process/2026-10-16-codex-existing-source-acceptance.md)
- [Codex premature-exit and actual-image verification](evidence/verify/2026-10-16-codex-early-exit-regression.md)
Coding verifier completion follow-up: [decision](notes/proposed/feature/2026-10-16-four-coding-verifier-completion.md) and [verification](evidence/verify/2026-10-16-four-coding-verifier-completion.md).
- [Aider independent verifier](notes/proposed/process/2026-10-16-aider-independent-verifier.md)
- [Aider verifier evidence](evidence/verify/2026-10-16-aider-independent-verifier.md)

- [Aider hardened image recheck](evidence/verify/2026-10-16-aider-hardened-image-recheck.md)
- [OpenCode verifier decision](notes/proposed/process/2026-10-16-opencode-verifier-completion.md)
- [OpenCode verifier evidence](evidence/verify/2026-10-16-opencode-verifier-completion.md)
- [Documentation ownership](notes/proposed/process/2026-10-18-template-documentation-ownership.md)
- [Canonical cleanup decision](notes/proposed/process/2026-10-16-express-cleanup-outcome.md)
- [Canonical cleanup evidence](evidence/verify/2026-10-16-express-cleanup-outcome.md)
- [Canonical Express CI decision](notes/proposed/process/2026-10-16-canonical-express-ci.md)
- [Canonical Express CI preparation](evidence/verify/2026-10-16-canonical-express-ci.md)

- [Integrated23 acceptance](notes/proposed/process/2026-10-18-integrated-template-acceptance.md) · [verification](evidence/verify/2026-10-18-integrated-template-acceptance.md)

- [Accepted Node startup repair](notes/implemented/process/2026-10-18-node-startup-race.md) · [verification](evidence/verify/2026-10-18-node-startup-race.md)
- [Accepted registry artifact retirement](notes/implemented/process/2026-10-18-orphan-registry.md) · [verification](evidence/verify/2026-10-18-orphan-registry.md)

- [Local Express/model review](evidence/verify/2026-10-18-local-express-model-review.md)
- [OpenCode completed-step decision](notes/proposed/process/2026-10-18-opencode-completion-steps.md)
- [Image CI checkpoint decision](notes/proposed/process/2026-10-16-image-ci-checkpoint.md)
- [Image CI checkpoint evidence](evidence/verify/2026-10-16-image-ci-checkpoint.md)
- [Prewarmed server configuration](notes/proposed/process/2026-10-16-prewarmed-server-configuration.md) · [verification](evidence/verify/2026-10-16-prewarmed-server-configuration.md)

- [Delivery integration review](evidence/verify/2026-10-18-template-delivery-review.md)

- [Consumer entry compatibility](notes/proposed/process/2026-10-19-consumer-entries.md) · [verification](evidence/verify/2026-10-19-consumer-entries.md)

- [Native acceptance entry](notes/proposed/process/2026-10-19-native-acceptance-entry.md) · [verification](evidence/verify/2026-10-19-native-acceptance-entry.md)
