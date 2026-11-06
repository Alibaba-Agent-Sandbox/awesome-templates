# Managed template integration with the independently published contract

Date: 2026-11-06
Result: PARTIAL

## Scope and identity

The existing PR296 branch at `ce09b53c89fdd780a6cdc9c0e1d26a14726be10d`
was pushed normally, then merged with contract main
`31fe653c2940d8681b9549be3f570977152847a7`. No shared history was rewritten.
The contract schema remains SHA-256
`3cce2cfc36a284ee2e84bce977bd22090b9419e991a5371854c96e74d12ec479`.

This integration retains the contract's complete temporary-fixture checker
regression and independent file-loader regression. The branch now implements
the declared managed startup, so the earlier contract-only rejection of every
valid managed profile is superseded by strict invalid-profile rejection before
imports, port selection or child startup. Existing spec5 argv remains unchanged.

The local runner reads its sibling checker/validator by fixed file origin with
non-main run names, retaining the canonical duplicate-key YAML reader without
changing sys.path or relying on CWD/package imports. Regressions call the actual
startup helper through an isolated Python importlib load from another directory,
and through the package entry point. Bilingual documentation retains the static
contract/deployed-runtime distinction and the branch's VPC/trust/cleanup guidance.

## Executed checks

- `python scripts/test_spec_tools.py`: **52 tests passed**, zero failures.
  Printed invalid-manifest/process-timeout diagnostics belong to deliberate
  negative cases, not failed suite results.
- `python scripts/check_template.py --all`: **48 conformant directories**, zero
  failures, including the new managed recipe and the existing skeleton/catalog.
- `python scripts/check_docs.py`: **232 documents**, zero failures after the
  scoped public documentation and engineering-record index updates.
- `python -m pytest agents-api/test_smoke.py -q`: **7 passed**. The pytest-asyncio
  default-loop-scope deprecation warning is retained as an environment warning.
- Actual local `_run_one` calls for **agents-api, python-hello and node-web** all
  passed. The legacy Python fixture reports20 assertions; Node reports60. These
  are local service/process tasks, not cloud acceptance or a full-catalog L0 rerun.
  After the final strict-reader change, agents-api and python-hello were repeated
  and passed; no Node runtime behavior changed.
- The local source/candidate server environment reports distribution0.4.0a7 and
  managed module SHA-256
  `ea8469547b6e9414fe5142d0917803112404a38deaff1b46559bdac1386fd265`.
  This is not a claim of PyPI availability.
- `git diff --check`: exit0 after conflict resolution.

The local servers, Node development/build processes, generated fixture workspaces
and managed scratch state were stopped/removed by their owned cleanup paths. No
cloud resources or model tasks were created by these checks.

## Remaining gates and preserved boundaries

Public recipes and the existing CI install continue to pin the actually available
a6 distribution in this checkpoint. Their missing-new-module caveat is retained.
Update those pins only after a real compatible release, then run the public
archive/image/deployment/model path. Historical source-only and earlier image
failure records are unchanged. Current CI/review, package publication and final
Provider/model/independent cleanup remain separate required delivery gates.

Refs: [template PR296](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/296),
[Issue295](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/295),
[independent contract](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/commit/31fe653c2940d8681b9549be3f570977152847a7).
