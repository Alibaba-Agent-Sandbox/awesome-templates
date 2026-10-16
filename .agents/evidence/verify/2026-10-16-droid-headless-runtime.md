# Droid headless runtime verification — 2026-10-16

Result: PARTIAL

Scope: `droid/{Dockerfile,commands.py,e2e_test.py,template.yaml,README.md,README.zh-CN.md,test_commands.py,test_e2e_protocol.py}`, `docs/design/droid.md` and this change's engineering records. Base repository revision: `2acb53481739e9585803076dd4c05ce5c2048219`; tested uncommitted scoped files. Existing work in other templates/shared files was preserved.

Environment: Linux x86_64, isolated Python 3.13.13, server/client distributions reporting 0.3.0, httpx 0.28.1 and pytest 9.1.1. The installed SDK checkout was `bb7881dc703ccdc3b97ff5ad67bcb129c4ea80ea`. Node 22.22.2 with isolated npm 10.9.4 installed the exact Factory release under a temporary prefix. No model credentials were forwarded to either local HTTP process.

## Executed validation

- PASS: fetched npm registry exact-release metadata: `@factory/cli@0.241.1`, bin `droid`, Node requirement `>=20.0.0`. Official [Droid Exec documentation](https://docs.factory.com/droid-exec/overview) confirms headless mode and autonomy flags.
- PASS: `node <isolated-npm10-cli> install --prefix <temporary-prefix> --no-audit --no-fund --cache <temporary-cache> @factory/cli@0.241.1` (exit 0). The system npm attempt failed before installation with `Class extends value undefined`; the isolated npm was used without modifying system tools.
- PASS: actual `droid --version` returned `0.241.1` (exit 0); actual `droid exec --help` (exit 0) lists `--auto low|medium|high` and `--cwd`. A clean-home, no-key `droid exec --auto low -- --literal-prompt` probe returned exit 1 with the expected authentication diagnostic and no unknown-option error; response content was not retained.
- PASS: `python -m pytest -q droid/test_commands.py droid/test_e2e_protocol.py`: 17 passed (exit 0). Tests include real child processes and owned descendant termination; the protocol fixtures are explicitly mocked and are not product E2E evidence.
- PASS: `python scripts/check_template.py droid`: `conformant: droid` (exit 0).
- PASS: targeted `scripts/run_local_e2e.py::_run_one` for the actual Droid template with the real pinned CLI on PATH (exit 0). The runner started the real SDK HTTP server and executed e2e_test.py. Ten HTTP checks passed: health, command signatures, 400/404, three invalid-value guards, actual target version, setup and target missing-key guard. L3 was explicitly NOT RUN.
- PASS of failure guard, not L3 acceptance: started another real SDK HTTP server with no model keys, then ran e2e_test.py with `E2E_RUN_LLM=1 E2E_REQUIRE_LLM=1`. The same no-key checks passed and the required L3 exited 1 with `target FACTORY_API_KEY is missing` (expected). This deliberately failing model acceptance prevents a false completion claim.
- PASS: `git diff --check -- droid docs/design/droid.md` (exit 0).
- PASS: repository-relative Markdown links in both READMEs, the design and these engineering records resolve (exit 0). A scoped scan of 11 source/document/record files against configured credential values found no matches; no values were printed or retained.

## Remaining gates

- BLOCKED: L1 Docker image build and L2 Express template deployment, because no usable Docker engine is available in the current managed environment. No cloud or image pass is claimed.
- BLOCKED: genuine L3 Factory model/coding acceptance, because the target Factory product credential is absent. Another provider's key cannot replace it. The full remote-file/process acceptance path exists and is regression-tested, but has not passed against Factory.
- NOT RUN here: repository-wide L0/spec checks and shared workflow/catalog reconciliation, assigned to the integration owner; results must be recorded separately after integration.
- NOT COMPLETE: independent review, commit, remote PR and required CI/merge. Reuse [issue #19](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/19); no duplicate Issue was created.

## Resource cleanup and claims

The two local servers were stopped by the existing runner cleanup. The process-tree regression proved its owned descendant did not write after timeout. No cloud template or sandbox was created; no model call was made. Temporary CLI dependencies remain outside the repository for integration checks. No provider evidence JSON was written, `tested_on` remains empty, and both READMEs list no verified provider.
