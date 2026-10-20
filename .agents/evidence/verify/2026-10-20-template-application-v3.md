# Template application v3 verification

Status: PARTIAL — local contract/checker scope; no cloud or publication claim.

Scope: clean task worktree from awesome-templates `ae375fb` (origin/main at checkout),
branch `feat/template-application-v3-20261020`. Changes comprise canonical v3 schema,
checker/semantic validator, contract regressions, pinned checker dependencies,
CI dependency installation, configuration fixtures, bilingual specification and records.
Existing template images, commands, versions, receipts and catalog status are unchanged.

Environment: Python 3.13.13; PyYAML 6.0.3; jsonschema 4.26.0. Dependencies were already
present in the isolated design validation virtualenv; no package resolution or
cloud command was needed. Commands below used that environment's Python.

## Actual verification

Final scoped commands all exited 0. Canonical schema SHA256:
`18e3c6bbc7b1ae462d8fb8294dd3859e7fb44a9ff67efe51c1383d3e70077c83`.

- `python scripts/test_spec_tools.py`: PASS, 52 tests, including 13 application-contract tests (14.198 seconds).
- `python scripts/check_template.py --all --strict`: PASS, all 26 template directories, zero violations.
- `python scripts/check_docs.py`: PASS, 126 Markdown documents, zero broken local targets.
- `python scripts/check_docs.py .agents/notes/proposed/architecture/2026-10-20-template-application-v3.md .agents/evidence/verify/2026-10-20-template-application-v3.md`: PASS, both new record documents, zero broken local targets.
- `git diff --check`: PASS, no whitespace errors.

Regressions use temporary local sources and synthetic deployment harness outputs.
They prove validation/controller behavior, not FC/Express execution or real model behavior.
The inline FC fixture deliberately contains an unavailable sentinel component pin
and replacement fields; it is structural input and must not be deployed as supplied.
The fixture lock is explicitly nonexecutable; the CLI owns real lock validation.

## Remaining gates and cleanup

BLOCKED: remote Issue/PR/check/review/merge depend on available authenticated GitHub
publication. No remote state is claimed. CLI parity/integration belongs to its own PR.
No provider/model credentials or cloud services were used. Runtime/image/provider L0–L3
were not executed because no runtime/image/provider claim changes in this repository.
No cloud resources were created; synthetic harness resources exist only in temporary tests.
