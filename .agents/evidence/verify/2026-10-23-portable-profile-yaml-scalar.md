# Portable profile YAML scalar correction

Result: PASS (local parsing scope); native workflow rerun required.

Issue: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/194. Source scope: `python-hello/template.yaml`, on top of 352bfe5c7f84baeb6e14b6e1868e7509e1ea6c4f.

## Actual cross-consumer failure

OpenSandbox T4 run https://github.com/Alibaba-Agent-Sandbox/awesome-providers/actions/runs/39939154965 passed real backend startup, plugin/installed contract checks, Python SDK scenarios and CLI lifecycle/files. The final source application launch failed before preparation because the CLI's real YAML 1.1 loader parsed the bare scalar `context: .` as numeric NaN. Python's YAML loader had accepted it as a string, so Python-only schema checks missed the difference. Cleanup completed successfully. That run did not certify the source application workflow.

The portable profile now explicitly quotes its root context as `context: '.'`. Its intended root-only context, Dockerfile, image and workflow behavior are unchanged. No provider or CLI validation was relaxed.

## Executed verification

- Actual built CLI `dist/utils/yaml_io.js` `loadYaml` on the old pinned manifest: reproduced `{dockerfile: 'Dockerfile.portable', context: NaN}`.
- Actual CLI loader on the corrected complete manifest plus strict `assert.deepEqual`: PASS, exact `{dockerfile: 'Dockerfile.portable', context: '.'}`.
- `python -m pytest -q scripts/test_workflow_contract.py scripts/test_managed_catalog.py`: PASS, 37 tests.
- `python scripts/check_template.py python-hello`: PASS, conformant.
- `git diff --check`: PASS.

The CLI owner is adding an actual YAML profile launch regression in its repository. The provider T4 template source pin must advance to this commit and rerun real source build, application invocation and prepared-image consumption; this parsing result is not native acceptance.
