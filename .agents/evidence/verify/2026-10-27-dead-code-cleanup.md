# Verification: Scoped unused-code cleanup

- Date: 2026-10-27
- Issue: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/240
- Base revision: `961959470411c3375a8346eb43755fa183129c22`
- Functional patch SHA256: `a7befe9d237c3df30efe79996969e916aa0f2dde15535df3c34b9d75d054afff` (Git binary diff against the base, excluding records/docs/changelog).
- Result: BLOCKED
- Environment: Linux; Node 22.22.2, TypeScript 5.9.3, ESLint 10.12.0; final Python checks use system Python 3.13.13; Ruff 0.17.3.

## What was verified

The scoped deletion preserves observable behavior, public contracts, generator ownership and historical evidence. Work is isolated from pre-existing workspace edits. Scope is the functional patch above plus its bilingual documentation, changelog where applicable, decision and evidence; current-head CI will bind verification to the pushed commit.

## Commands and results

| Command / check | Result | Evidence |
| --- | --- | --- |
| Changed-file AST parse and F401 review | PASS | 69 files parse; 131 unused imports removed. Imported unittest TestCase discovery is preserved with an explicit annotation. |
| `python scripts/test_spec_tools.py` | PASS | 39 tests after restoring imported TestCase discovery. |
| `python scripts/check_template.py --all` | PASS | No nonconformant template; zero claimed-spec failures. |
| `python scripts/check_docs.py` | PASS | 222 documents, zero failures before final evidence update. |
| `python scripts/sync_process_runners.py --check` | PASS | All 15 canonical copies match. |
| Affected pytest regressions, per-directory invocation | PARTIAL | 23 of 28 directory groups pass; remaining results below. |
| `E2E_RUN_LLM=0 python scripts/run_local_e2e.py` | FAIL locally | 37 groups pass, 10 fail out of 47. Model-execution skips remain skips. |

The per-directory regressions retain these limitations: browser-automation (5 failed/8 passed) and chrome (10 failed/16 passed) need browser/MCP components; dev-services (5 failed/7 passed) needs pinned PostgreSQL/Redis; next-app (4 failed/10 passed) needs pinned native dependencies; scripts exceeded the 180-second scoped timeout during filesystem-heavy fixtures. A separate direct spec suite passed. Initial process-test failures under downloaded Python 3.12 were rerun with system Python 3.13, which exposes the required memfd/pidfd APIs. A spec test initially raced with temporary pytest cache files; the isolated rerun passed. The initial 23-test result omitted dynamically imported TestCase tests; it is superseded by the restored-discovery 39-test run, not used as complete coverage.

The ten L0 failures were agents-cli (installed version pins), apply-patch (Codex pin), browser-automation (required Chromium), claude-code (original ELF/version), code-server (version pin), media-tools (lossless conversion/independent PCM assertion), next-app (toolchain version HTTP 500), opencode (CLI/setup/authenticated target startup), qoder and qwen-code (version pins). These failures remain recorded; no image, cloud deployment or real model acceptance is claimed. The media conversion failure is not attributed to a missing tool: its FFmpeg version check passed, but the artifact assertion failed.

## Scope and further analysis

Runtime implementations, Dockerfiles, manifests, dependency pins and generated runners are unchanged. Remaining wider candidates comprise 55 runtime/support F401 findings and four F841 findings. Generated `process.py` copies must be changed through `scripts/process_runners`. The four assignments perform private package copying, URL-port validation, image access and a Git fixture read respectively; removing the call/property access could change behavior. The imported ApplicationContractTest is dynamically discovered by unittest and remains. Ruff 0.17.3 misparses a semicolon followed by the variable name `match`; Python AST/compilation accepts it, so no source syntax fix is justified.

An isolated AST-prefix probe of the default agents-cli SDK factory raises `NameError: Sandbox` with zero network calls. The original main imports ProviderSandbox but assigns an undefined Sandbox. This pre-existing defect is tracked separately: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/241.

## Cleanup and remaining gates

The local runner owns and stops its per-template HTTP processes; no cloud resources or model operations were created by this validation. Current-head CI with its declared native prerequisites remains required. No fresh provider/image/model qualification is implied by import-only maintenance. The PR remains draft while local/remote mandatory checks are unresolved.
