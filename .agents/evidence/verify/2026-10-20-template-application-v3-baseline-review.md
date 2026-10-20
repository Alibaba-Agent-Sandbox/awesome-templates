# Application provider feature baseline review

Status: PARTIAL — local contract validation passed; remote/cloud gates unchanged.

Scope: follow-up to local `1ee8286` on `feat/template-application-v3-20261020`.
The CLI review found its real runtime feature preflight was stricter than the
canonical template schema. The schema now requires `sandbox.lifecycle` in both
modes; external mode additionally requires `exec.run` and `files.rw`, while local
mode requires `ports.url`. Fixtures/docs and a negative regression agree. No
existing runtime, image, catalog status or historical verification file changed.

Environment: Python 3.13.13, PyYAML 6.0.3, jsonschema 4.26.0, same isolated environment
as the original verification. Current schema SHA256:
`889f077e438c85a903193583d325b7edebcdaef86f1496642dd77056a058945f`.

Actual command results (exit 0):

- PASS `python scripts/test_spec_tools.py`: 53 tests including 14 application contract tests.
- PASS `python scripts/check_template.py --all --strict`: all 26 directories conformant.
- PASS `python scripts/check_docs.py`: 126 documents, zero broken local targets.
- PASS scoped new record-link check and `git diff --check` before commit.

Regressions use synthetic local inputs; no cloud resources, credentials, hooks,
images or model calls. No owned cloud cleanup is needed. Authenticated remote
publication, current-head CI/review/merge and any real FC acceptance remain unrun;
this record does not certify those independent gates.
