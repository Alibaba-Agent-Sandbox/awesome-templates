# Application profile defaults verification

Status: PASS for local contract/checker checks; publication and compatible CLI
consumer delivery remain separate. No new cloud/runtime/model claim is made.

Baseline: `e94ab308a74715982bb059b142518f7d6070c1c2`.
Python 3.11.15; spec dependencies PyYAML 6.0.3 and jsonschema 4.26.0 installed from
`scripts/requirements-spec.txt` in an isolated environment. Pytest 9.2.0 was used
for the existing local tests. Node executes the same JSON fixtures as Python.

- `python scripts/test_spec_tools.py`: PASS, 58 tests; includes 8 shared fixture
  cases in both languages and actual compact manifest equivalence.
- `python scripts/check_template.py --all`: PASS, no claimed spec failures.
- `python -m pytest -q scripts/test_check_docs.py scripts/test_managed_catalog.py scripts/test_template_launch_contract.py`: PASS, 40 tests.
- `python scripts/check_managed_catalog.py`: PASS, zero violations.
- `python scripts/sync_launch_contracts.py --check`: PASS.
- `python scripts/sync_process_runners.py --check`: PASS, 15 helpers unchanged.
- `python scripts/sync_controller_ownership.py --check`: PASS, 8 controllers unchanged.
- `python scripts/check_docs.py`: PASS, 234 documents and zero local link failures
  at final review.
- `git diff --check`: PASS; repeated at review.

The first documentation run failed because this environment's checkout ownership
triggered Git safe-directory checking. Re-running with a process-local exact
safe-directory setting passed; no repository or global ownership policy changed.

Only agents-api's manifest changes; version becomes 0.1.5. The expanded contract
matches the prior authored fields exactly apart from that version. No images,
server code, existing provider receipts or ordinary template manifests change.
No real deployment, model execution, provider qualification or resource creation
was attempted. Existing historical evidence is not rewritten as a new pass.

Additional required Sandbox features remain supported beyond the two profile defaults;
producer and Registry regressions explicitly preserve this existing extension point.
