# Release integration verification — 2026-10-24

Result: PARTIAL

## Candidate and scope

Integrated the prior release fixes on current main `cb8800159d170198a31e03d4e5cf06d4cf92133b`; code commit `dd2be31` contains the integration. Preserved the newer managed workflow service/operation/startup validation and its strict schema documentation. Resolved bilingual specification conflicts by retaining current managed semantics and appending only the server-pin requirement. Previous evidence remains history.

Tracking: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/199.

Environment: Python 3.12.13, Node 22.22.2; isolated environment installed `scripts/requirements-spec.txt` (PyYAML 6.0.3 and jsonschema 4.26.0), pytest 9.1.1, httpx 0.28.1, and the previously built release-candidate server package from the Python SDK candidate `ddc96d8ee237ad1de5348f08612b9aceefa431b7`. This is local source validation, not a PyPI installation claim.

## Passed locally

- `python scripts/test_spec_tools.py`: 58 passed, exit 0.
- `python scripts/check_template.py --all`: no nonconformant directories, exit 0.
- `python scripts/check_docs.py`: 221 documents, 0 failures, exit 0.
- `python -m pytest -q scripts/test_ci_image.py scripts/test_source_image_acceptance.py scripts/test_workflow_contract.py scripts/test_managed_catalog.py`: 93 passed, exit 0.
- `python -m pytest -q qwen-code/test_commands.py qwen-code/test_e2e_protocol.py`: 70 passed, exit 0.
- `python -m pytest -q scripts/test_prepare_steps.py -k 'server_pin or preparation_binds or all_catalog_profiles'`: 3 passed, 18 deselected, exit 0. Includes complete catalog profile preparation.
- `git -c core.filemode=false diff --check`: passed.

The checksum-verified Node 24.16.0 / Qwen 0.23.0 installation smoke remains the dated previous report; it is not presented as rerun today. The same bytes and pin values were retained.

## Remaining gates and qualification

`python scripts/source_image_acceptance.py` exits 1 with `complete: false`: 46 current source templates, zero matching current Express runtime, Express HTTP, or OpenSandbox native HTTP qualifications. This is a qualification gap, not a passing runtime check. Four managed entries are separately validated and do not inflate the source total.

Docker is unavailable locally. New image builds and exact-source native/model acceptance were not run here; historical receipts do not certify changed manifests/build contexts. Remote image CI and required review must pass before the relevant merge/release gates can be closed. No cloud resources, template publication, or merge is claimed by this record.
