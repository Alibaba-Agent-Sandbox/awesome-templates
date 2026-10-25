# Unified template launch verification

Status: PARTIAL — local contract checks pass; cross-repository consumer publication, CI and current-format cloud launches remain pending.

## Scope

Base revision: `ac1ac52c3a0b60c59b8e022fbf0b5f26061fca70`. Scoped branch: `refactor/unified-template-launch`. The changes migrate 46 source catalog manifests, one skeleton, two deployment examples and four managed catalog entries to specification 5. Runtime commands, Dockerfiles, dependencies, start/readiness commands and provided services remain unchanged.

Issue: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/212

## Executed local checks

Environment: Linux, Python 3.13, isolated environment with `scripts/requirements-spec.txt`, pytest 9.1.1 and httpx 0.28.1.

- PASS: `python scripts/test_spec_tools.py` — 58 tests.
- PASS: `python -m pytest -q scripts/test_managed_catalog.py scripts/test_template_launch_contract.py scripts/test_public_launch_e2e.py scripts/test_template_application.py scripts/test_check_docs.py` — initial run 75 tests and 92 subtests. The subsequent shared-lock check is recorded below after synchronization.
- PASS: `python scripts/check_template.py --all` — 47 directories, zero claimed-spec failures.
- PASS: `python scripts/check_docs.py` — initial run 222 documents, zero local-link failures. New records and shared contract links require the final rerun below.

The public launch harness validates the complete specification 5 source manifest and invokes `template launch` without a workflow selector. Local harness tests use synthetic responses; they are not cloud passes.

## Remaining gates

Current-head remote CI, actual new-format provider launches and independent cleanup, compatible CLI/SDK installation provenance, cross-repository merge sequence. Historical 2026-10-24 cloud matrix receipts remain immutable and do not certify these changed manifests.

## Final local contract checks

- PASS: shared launch contract synchronized from Python SDK `283ff91dae79ffaf0e27c5503b1c7788bdc26de7`, checked against its committed bytes and recorded in `spec/contracts/launch-source-lock.json`.
- PASS: `python scripts/sync_launch_contracts.py --check`; the source schema specification, retired fields and service fields agree with the canonical contract.
- PASS: `python scripts/sync_workflow_contracts.py --check`; immutable historical receipt contracts remain readable without imposing old workflow authoring fields.
- PASS: final targeted pytest command above — 76 tests and 92 subtests.
- PASS: `python scripts/check_managed_catalog.py` — four managed entries, zero violations.
- PASS: final `python scripts/check_docs.py` — 222 documents, zero local-link failures.
- PASS: semantic comparison against the base commit — all 49 source/example manifests retain every field except the intentionally migrated specification/workflow fields; all four managed entries retain their native identities and service declarations; source catalog metadata is unchanged.
- PASS: `git diff --check`.

No cloud deployment was performed by this local verification run. No task resources were created, so cloud cleanup does not apply to these local checks.

## Candidate-source matrix entry

The existing manual public-launch workflow now accepts `distribution=source` for reviewed pre-release consumers; its default remains `published`. Source mode uses lockfile-based CLI installation/build and installs both Python packages from their exact checked-out commit. Reports explicitly record source distribution and exact template/CLI/SDK/provider commits and omit npm/PyPI registry claims. Published mode retains package-version verification.

- PASS: `python -m pytest -q scripts/test_public_launch_e2e.py` — 22 tests, including source-versus-published provenance and unknown distribution rejection.
- PASS: documentation links and whitespace validation rerun after this addition.
- NOT RUN locally: Docker-backed cloud matrix; this environment has neither Docker executable/socket nor an OpenSandbox endpoint. The GitHub runner supplies its own Docker-backed OpenSandbox fixture. Existing Express secret configuration is used only by the original workflow; no new credentials were uploaded.
