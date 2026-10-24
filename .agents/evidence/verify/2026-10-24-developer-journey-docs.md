# Verification: Public developer journey documentation

- Date: 2026-10-24
- Result: PARTIAL — local checks and final CI/public readback recorded below as they complete.
- Issue: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/201
- Scope: bilingual documentation and engineering records; runtime code, template recipes and package versions unchanged.

## Baseline observation
Published CLI 0.4.11 and Python client 0.3.1a1 were exercised against real Express resources. A manually prepared python-hello steps manifest reached READY, then named commands, external HTTP, file hash round-trip, processes and a real PTY passed. The default Docker path lacked a local Docker installation. Initial incorrect --json info and unattended rm calls were corrected according to help; those invocation errors are not classified as product defects.

## Cleanup
Both owned sandbox and template were deleted; independent exact-ID reads reported sandbox not found and template HTTP 404. No list-emptiness inference was used.

## Local checks
- PASS: `python scripts/prepare_steps.py python-hello --output <fresh-directory>` produced 9 explicit steps without a cloud call.
- PASS: `python scripts/check_template.py python-hello` (repository-pinned requirements installed in an isolated environment).
- PASS: `python scripts/check_docs.py`: 221 documents, zero link failures.
- PASS: `python -m pytest -q scripts/test_check_docs.py`: 4 passed.
- Initial checker invocation lacked the pinned jsonschema dependency; after installing `scripts/requirements-spec.txt`, the same check passed.

## Remaining gates
Record local check results, latest-head CI, public documentation readback, and the post-publication rerun. No post-publication success is claimed here.
