# Verification: independent managed manifest contract

- Date: 2026-11-06
- Change: [Issue298](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/298), independent producer extracted from reviewed commit `6c0bd346d94ed888d3c2674309d73e13474363a6`.
- Result: PARTIAL — required local checks pass; current-head CI/review and merge remain pending.
- Environment: Linux, isolated Python environment with the pinned `scripts/requirements-spec.txt`.
- Scope: schema, static checker, independent fixtures, legacy-runner rejection and bilingual contracts only.

## What was verified

Schema bytes remain SHA-256 `3cce2cfc36a284ee2e84bce977bd22090b9419e991a5371854c96e74d12ec479`.
No agents-api source directory or catalog entry is included. The acceptance owner independently
reviewed the split, SDK-free fixtures and fail-closed legacy-runner boundary before implementation.

## Commands run

```bash
python -m venv "$CONTRACT_VENV"
"$CONTRACT_VENV/bin/python" -m pip install -r scripts/requirements-spec.txt
"$CONTRACT_VENV/bin/python" scripts/test_spec_tools.py
"$CONTRACT_VENV/bin/python" scripts/check_template.py --all
"$CONTRACT_VENV/bin/python" scripts/check_docs.py
"$CONTRACT_VENV/bin/python" -m pip install httpx==0.28.1
"$CONTRACT_VENV/bin/python" scripts/test_public_launch_e2e.py
"$CONTRACT_VENV/bin/python" scripts/test_canonical_express_review.py
"$CONTRACT_VENV/bin/python" scripts/test_local_cleanup.py
git diff --check
```

## Results

The first run with the base interpreter stopped with the existing controlled missing-PyYAML
diagnostic. Dependencies are installed in an isolated environment rather than changing global
packages. The supplemental public-launch regression suite initially reported 14 errors because
its optional httpx dependency was absent; installing the same exact HTTP client pin used in CI
resolved that environment prerequisite without a product change.

| Check | Result | Scope |
| --- | --- | --- |
| Specification tools | PASS | 48 regressions, including independent managed checker/guard cases and preserved v5 behavior |
| Complete checker | PASS | All 47 existing root manifest directories; no catalog change |
| Documentation links | PASS | 227 documents, zero failures |
| Public-launch controller regressions | PASS | 42 local tests; no real cloud call |
| Canonical authorization regressions | PASS | Six local tests; explicit no-cloud boundary retained |
| Local cleanup regression | PASS | One local test |
| Scoped diff and exact schema bytes | PASS | No v5 schema, template directory, catalog or acceptance/image workflow changes |
| Latest-head CI and merge | PENDING | Required before producer delivery |


## Cleanup and limitations

Temporary regression fixtures clean up through unittest. No SDK/runtime/image was installed,
no cloud/model call was made, and no remote resource was created. This evidence does not verify
an Agents API recipe or authorize qualification of a provider. The full template Issue295 remains open.
