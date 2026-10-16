# Engineering records: awesome-templates

This repository owns template source, specification, catalog and acceptance records.
Read [CONTRIBUTING.md](../CONTRIBUTING.md) and [the specification](../docs/template-spec.md).
New engineering records use English and stay in this repository.

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

- [Catalog completion decision](notes/proposed/feature/2026-10-16-catalog-completion-review.md)
- [Verification](evidence/verify/2026-10-16-catalog-completion-review.md)
- [Image-build gate](notes/proposed/process/2026-10-16-template-image-build-gate.md)
- [Image-build preparation evidence](evidence/verify/2026-10-16-template-image-build-gate.md)

- [OpenCode verifier decision](notes/proposed/process/2026-10-16-opencode-verifier-completion.md)
- [OpenCode verifier evidence](evidence/verify/2026-10-16-opencode-verifier-completion.md)
