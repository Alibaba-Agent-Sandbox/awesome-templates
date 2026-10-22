# Verification: remove retired project compatibility

- Date: 2026-10-22
- Result: PARTIAL (remote acceptance pending)
- Revision: scoped files in branch `refactor/remove-legacy-20261022`; the containing commit is the reviewable source revision.
- Environment: Linux, Node.js 22.22.2; Python 3.11.15 in an isolated environment.
- Issue: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/187

## What was verified

Retired project APIs, migration fields and fallbacks are removed rather than forwarded. Tests and bilingual documentation describe one current contract. Historical engineering evidence is preserved.

## Commands and results

- PASS: `python -m unittest discover -s scripts -p 'test_spec_tools.py'` — 43 tests, including rejection of a missing spec version with `--all`.
- PASS: `python -m unittest discover -s scripts -p 'test_*.py'` — 90 tests after installing the existing preview requirements. An earlier broad attempt lacked aiohttp and is superseded; the first hash-enforced install rejected an unpinned transitive requirement, so the existing requirements file was installed with its normal supported command.
- PASS: `python scripts/check_template.py --all` — all 46 checked templates conform, zero violations.
- PASS: `git -c core.filemode=false diff --check`.
No template's backend acceptance or maturity has been promoted; this change verifies the checker against real repository files and malformed temporary metadata.

## Outstanding gates

Required remote CI, review and merge are not established by local results. Initial Git invocations had not loaded the ignored workspace credential file; authenticated fetch and GitHub access now succeed. No package release or manual production deployment is requested. Cross-repository consumers must land after their shared contract.

## Cleanup

Local fixtures use owned temporary resources. The Python cloud fixture tracks and cleans its own sandbox resources. No raw credentials or sensitive logs are included. Native checks that did not execute are not passes.

## Remote CI correction

The first local-e2e workflow still invoked the removed `--strict` selector and failed at checker invocation. The workflow now invokes `--all` directly. The current Express harness and its fixtures use plain official template list/info commands without removed API selector flags. Their unit tests are rerun before the follow-up commit. Immutable, explicitly authorized historical review pins remain unchanged.
