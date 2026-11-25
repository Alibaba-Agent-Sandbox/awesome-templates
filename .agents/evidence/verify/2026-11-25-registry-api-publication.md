# Verification: Registry API publication contract

- Date: 2026-11-25
- Result: PASS (publication/parser scope)
- Baseline: awesome-templates 55efccb6d72b18a9360f0599621b207e97a82396
- Issue: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/317
- Dependencies: scripts/requirements-spec.txt installed in an isolated Python 3.13 environment.

## Checks

- `python scripts/test_registry_api.py`: 7 tests passed with real local YAML/filesystem/schema/checker behavior.
- `python scripts/test_spec_tools.py`: the original full run passed 65 tests; two additional reference/size regressions were then added and passed in the focused 7-test suite. Final aggregate rerun recorded below.
- `python scripts/check_template.py --all`: all 48 catalog/skeleton directories conform; zero failures.
- `python scripts/check_docs.py`: 238 current documents, zero broken links at the initial checkpoint. Final document/record rerun follows below.
- `python contracts/template-v1/test_contract.py`: 14 tests passed. The resource contract remains inactive.
- Real cross-repository integration: the bilingual guide's two YAML blocks were loaded through the canonical validator by Registry build_templates. The resulting summary contained only API name/resource/port/local path and operationId/method/path; security scheme names and values were absent.

## Review

Round 1 identified the missing producer contract and rejected a wholesale unverified resource migration as a prerequisite. Round 2: the CLI API reviewer and root independently reviewed package containment, API limits, reference traversal and metadata projection; no blocking divergence found. Fixed an overbroad sentence: binding metadata does not start a server, while the template deployment can still perform its own startup. Added external-reference-in-schema and literal-example controls requested by root.

## Boundaries and original failed setup checks

The first test attempt used system Python without PyYAML; rerun used the repository's pinned dependencies. The first document check lacked a safe.directory scope for the isolated worktree; rerun applied process-scoped Git configuration and passed. A synthetic Registry integration fixture initially omitted the declared Dockerfile; corrected to copy the actual source recipe, after which integration passed. These were setup failures, not product passes.

Publication checks do not assert server reachability, permission, full OpenAPI invocation support, new resource-engine execution or cloud acceptance. No cloud resource, model task or secret was created. Current native component contracts and the broader draft migration remain separate.

## Final aggregate checkpoint

- `python scripts/test_spec_tools.py`: 67 tests passed after the final reference/size controls.
- `python scripts/check_docs.py`: 238 current documents, zero failures after record additions.

## Actual CI dependency correction

The initial head47ee1bee local-e2e job139101844091 failed in the new Registry tests with ModuleNotFoundError for yamlcore. Its manual dependency list installed only PyYAML/jsonschema, while the canonical contract job used scripts/requirements-spec.txt and passed. The follow-up changes checker jobs to the existing pinned requirements file; it does not weaken or skip the failing tests. The initial failure remains at https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/45584294163/job/139101844091 . Current-head CI must pass before merge.

## Narrow final CI dependency scope

Head63158c775ae09c11f857cb3b9d93bdbf7cd86529 passed all seven e2e jobs, including local-e2e: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/45585840953 . Its image workflow was unnecessarily broadened by editing the plan job: select_image_templates.py only reads YAML, while the actual image checker job already installs requirements-spec.txt. The canonical authorization job also does not load the API reader. Root cross-review therefore approved restoring those two unrelated workflow edits exactly to baseline, retaining only the local-e2e dependency correction. Final-head checks run independently. The superseded broad image run may be canceled to avoid redundant builds; canceled images are not passes.
