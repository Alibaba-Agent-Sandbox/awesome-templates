# Verification: current Express acceptance CLI contract

- Date: 2026-10-23
- Result: PASS for scoped controller/parser/cloud-helper verification. Final repository CI and merge are separate gates recorded in PR #193.
- Tested code head: 1cf28716775f (base 068119d022d96358a5031a35c0b6690f75e2fa13); final review also guards failed-create stdout as described below.
- Environment: Linux, Python 3.13.13, Node 22.22.2. Credentials only in ignored environment; no private IDs or raw cloud logs committed.

## Commands and results

| Check | Result |
| --- | --- |
| pytest scripts/test_express_cli_contract.py scripts/test_express_cleanup.py scripts/test_sdk_creation.py scripts/test_ci_image.py scripts/test_spec_tools.py | PASS: 94 tests, 186 subtests; one actual-executable test deliberately skipped in this no-ABX controller run |
| ABX-selected actual executable test_express_cli_contract.py | PASS: four cases before adding the separate timeout-unit case; actual list/create/kill/delete parser integration passed |
| New express-cli-contract CI job | PASS at tested head: all five current cases, immutable CLI source 6df41f624249c316654fbd5c6d36c34a7beca0b8 built with its lockfile |
| python scripts/check_template.py --all | PASS: no nonconformant templates |
| python scripts/check_docs.py | PASS: 218 documents, zero failed links |
| git diff --check | PASS |
| Real Express helper smoke | PASS: preflight, actual template inventory schema, positional detached create, strict ID parse, exec, normal kill helper and independent full list readback |
| Final independent full inventory | PASS: zero sandboxes listed; no owned resources leaked |

Actual-parser tests use help/invalid timeout and cannot mutate cloud resources. Controller tests cover preflight-before-deploy, malformed IDs/inventory, exact alias ownership, ambiguous create recovery, failed cleanup/readback, SDK mode and image readiness. A mismatched executable now exits BLOCKED with a safe actionable hint before build/deploy. SDK positive-timeout semantics stay intact; CLI timeouts below 30 seconds fail before deployment.

## Failures and boundaries

Parallel mounted-filesystem runs sometimes exceeded the 30-second help timeout; a separate actual parser run passed and the isolated CI integration passed. These timeouts are retained as environment failures, not product passes.

A first 60-second real helper smoke failed after create; short TTL under slow startup was only a hypothesis. The 300-second retry passed every stage and independent cleanup; a final full list was empty. Recovery journal removal followed confirmed absence. No template or image was created in these helper probes.

The immutable historical canonical workflow retains its pinned runner. Canonical cloud/image jobs skipped by their unchanged authorization/path gates are not counted as provider acceptance. No Codex Docker/ACR rebuild, new L1/L2/L3 qualification or template/runtime/model change is claimed. General diagnostic reporting remains a CLI design proposal, with no backend deployment.

This pre-merge receipt does not claim the pending complete repository workflow already finished. [PR #193](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/193) records final-head CI and actual merge; [CLI PR #110](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/pull/110) owns recovery/generator fixes and the reporting proposal review.

## Failed-create stdout review

A nonzero create result never supplies a trusted ID, even if stdout looks like one. The attempt remains ambiguous and recovers through the owned template, preventing normal cleanup from acting on an arbitrary diagnostic token. The same five-suite controller command passed again: 94 tests, 186 subtests, one deliberate no-ABX integration skip. Successful creation and cloud-helper behavior are unchanged.
