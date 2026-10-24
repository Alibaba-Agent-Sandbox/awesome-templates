# Release readiness verification — 2026-10-23

Result: PARTIAL

Base: fecb0ecb2fd6615132646f1e5c2a2460768a224a. Tested scope: thirteen template and skeleton Dockerfile pins, python-hello portable profile, template patch versions, bilingual README/design notes, server pin resolver/checker and their regressions. Historical evidence is unchanged.

Environment: Python3.12.13 isolated venv with scripts/requirements-spec.txt (PyYAML6.0.3/jsonschema4.26.0), pytest9.1.1, paired public server archive e2cb27e24fde0a67112f82b8d44af463445a5d1a and httpx0.28.1. Node22.22.2 for repository tooling; separately downloaded checksum-verified Node24.16.0 x64 for Qwen smoke.

## PASS

- `python scripts/test_spec_tools.py`:58 tests, exit0.
- `python scripts/check_template.py --all`:0 nonconformant directories, exit0.
- `python scripts/check_docs.py`:221 documents,0 link failures, exit0.
- `python -m pytest -q scripts/test_ci_image.py scripts/test_source_image_acceptance.py scripts/test_workflow_contract.py`:71 passed, exit0.
- `python -m pytest -q qwen-code/test_commands.py qwen-code/test_e2e_protocol.py`:70 passed, exit0.
- Official https://nodejs.org/dist/v24.16.0/SHASUMS256.txt agrees with both archive hashes in the Dockerfile. The x64 archive was downloaded, hashed and extracted; actual `npm install --prefix <temporary-prefix> @qwen-code/qwen-code@0.23.0` under this Node followed by `qwen --version` returned0.23.0, exit0. This is installation compatibility, not an image/model pass.

## Corrections and incomplete checks

The initial spec run failed because a malformed-pin regression replaced the old literal SHA after the skeleton pin changed. It now uses the resolver's source pin; the final58-test rerun passed. Initial Qwen test collection lacked httpx; after installing its exact documented dependency the70 tests passed. A broad preparation suite was interrupted rather than counted as passing; targeted pin/manifest checks are recorded separately.

`python scripts/source_image_acceptance.py` reports46 catalog entries and0 current Express runtime/HTTP/OpenSandbox qualifications. Current main already changed all workflow manifests; old records cannot certify those inputs, and this patch further changes13 build contexts. This is an expected qualification gap, not a new cloud pass. No old evidence was rewritten. The changed images need fresh exact-source image/workflow receipts.

Docker is unavailable in this environment. Full image builds, native backend workflow execution and real-model acceptance were not run. No cloud resources were created. No package or registry publication, remote CI/review or merge is claimed. The proposal remains pending these applicable gates.

Targeted preparation regressions: `python -m pytest -q scripts/test_prepare_steps.py -k "server_pin or preparation_binds"`:2 passed,19 deselected, exit0. The separate full-catalog preparation generator completed: `python -m pytest -q scripts/test_prepare_steps.py -k all_catalog_profiles`:1 passed,20 deselected, exit0 in147.77seconds.
