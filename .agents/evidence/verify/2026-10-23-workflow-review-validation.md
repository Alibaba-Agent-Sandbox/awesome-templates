# Workflow review validation

Date: 2026-10-23

Result: PASS (local specification/checker/documentation scope); remote PR checks
and merge remain pending.

Issue: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/197

## Scope and environment

Base: `fecb0ecb2fd6615132646f1e5c2a2460768a224a` from the current remote main.
The isolated change covers `scripts/template_application.py`,
`scripts/check_managed_catalog.py`, their workflow/managed regression suites,
`spec/template-v4.schema.json`, the bilingual template specification, changelog
and these engineering records. Python 3.11.15 with PyYAML 6.0.3,
jsonschema 4.26.0 and pytest 9.1.1 was used in an isolated review environment.

The original feature checkout and pre-existing user work were preserved.
No template manifest, Dockerfile, runtime, dependency or provider claim changed.

## Reproduction and regression

Before the implementation fix, the first four new regression cases failed.
Independent root review then reproduced the analogous missing startup-command
check, and its new regression failed before moving the check into the helper:

- A managed application selecting `commands.run` from a service providing only
  `commands.list` was incorrectly accepted.
- Managed exec and interpreter workflows carrying a `service` were accepted.
- A local application using the retired legacy profile was accepted.
- A managed workflow selecting exec startup without a command was accepted.

The application regression also adds the missing operation and verifies that
the corrected input passes; rejection is therefore specific to the mismatch.
The local profile regression confirms the current example passes first.

## Executed checks

- `python -m pytest -q scripts/test_managed_catalog.py scripts/test_workflow_contract.py scripts/test_template_application.py scripts/test_select_image_templates.py`:
  87 passed and 92 subtests passed; exit 0.
- `python scripts/test_spec_tools.py`: 57 tests passed; exit 0. The harness failure
  messages printed by negative tests are expected synthetic regressions, not
  actual cloud executions.
- `python scripts/check_template.py --all`: all 46 source templates and the
  skeleton conform; no failures; exit 0.
- `python scripts/check_managed_catalog.py`: no violations; exit 0.
- `python scripts/check_docs.py`: no broken local Markdown links; exit 0.
- `git -c core.filemode=false diff --check`: no whitespace errors; exit 0.

## Limits and resource ownership

These are schema, checker, selection and documentation results. They do not
certify a deployment, interpreter or image. No image/cloud tests were run and
no cloud resources were created. This follows the scoped verification table in
`docs/project-standards.md`; no image/runtime/provider qualification changed.
Historical receipts remain unchanged. Current-head remote CI and verified merge
must be recorded separately before claiming final delivery.
