# awesome-templates contributor instructions

This repository owns template implementations, specification, catalog and
acceptance records. SDK/server and CLI code belong to their independent repositories.

Before changing files, read [CONTRIBUTING.md](CONTRIBUTING.md),
[project standards and definition of done](docs/project-standards.md),
[documentation standards](docs/documentation-standards.md),
[the template specification](docs/template-spec.md), [.agents/README.md](.agents/README.md),
the PR/Issue templates, and any template-local `AGENTS.md`.

- Inspect the initial diff; preserve unrelated work and use an isolated task branch when needed.
- Use `_skeleton/`, pinned dependencies and the documented platform/non-root profile.
  Keep manifest, catalog, design, commands and both README languages consistent.
- All modified repositories need their own decision note and actual verification evidence.
  Keep historical evidence immutable and link template-local cloud receipts in place.
- Run `python scripts/test_spec_tools.py` and
  `python scripts/check_template.py --all --strict` for specification/catalog changes.
  Run `python scripts/check_docs.py` for documentation and targeted regressions for behavior.
  Runtime/image/model changes need the corresponding acceptance tiers and CI checks.
- Never infer provider verification from local/mocked/source-only execution. Record build
  mode, exact provenance, failures/skips and independently confirmed owned cleanup.
- Keep credentials, private endpoints and raw sensitive logs out of files and public discussions.
  Follow the security/reporting and license rules in the project standards.
- Reuse owner Issues, commit scoped Conventional Commits, use the PR template, push a task
  branch and merge after current-head checks and required reviews. Verify actual remote merge
  and Issue acceptance; do not bypass checks, force shared history or push directly to main.
  Honor explicit local-only, draft-only, review-only and no-merge requests.
