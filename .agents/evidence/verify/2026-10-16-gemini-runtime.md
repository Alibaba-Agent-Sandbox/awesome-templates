# Gemini runtime verification — 2026-10-16

Result: PARTIAL

Scope: `gemini/{Dockerfile,template.yaml,commands.py,e2e_test.py,README.md,README.zh-CN.md,test_commands.py,test_e2e_protocol.py}`, `docs/design/gemini.md`, `docs/usage-gemini.md`, and this task's repository records. Baseline HEAD: `2acb53481739e9585803076dd4c05ce5c2048219`; tested source includes the scoped uncommitted implementation. Existing unrelated template changes were preserved. Refs [Issue #30](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/30).

Environment: Linux, Python 3.13.13 in the prepared development virtual environment, Node v22.22.2. Pinned npm install used an isolated temporary prefix and npm 10; no platform permissions changed. Interpreter/prefix paths below are normalized to avoid machine-specific records. No root `.env` contents were read or recorded by this task.

## PASS — installed package and supported flags

Executed `node <npm10-cli> view @google/gemini-cli@0.64.0 engines bin --json`, then `node <npm10-cli> install --prefix <temporary-prefix> --no-audit --no-fund @google/gemini-cli@0.64.0`; both exit 0. Metadata: Node >=20, binary `gemini`. Executed that installed binary's `--version` and `--help`, exit 0; version exactly `0.64.0`. Actual help documents `-p` headless, `--model`, `--output-format json` and `--approval-mode plan|yolo`. It does not advertise a max-turns flag; the wrapper does not invent one.

## PASS — behavior and protocol regressions

With the isolated real pinned binary on PATH: `python -m pytest gemini/test_commands.py gemini/test_e2e_protocol.py -q`, exit 0, 18 passed. Covers actual setup/version preserving existing settings bytes/mode, synthetic secret redaction on success/failure, missing Gemini key refusing execution even with an unrelated OpenAI key, explicit approval flags, timeout/path ranges, symlink/traversal rejection, owned descendant termination, suppressed sensitive timeout traceback, forced-off zero requests, target-key detection independent of controller environment, and rejected false coding acceptance.

## PASS — checker and actual HTTP L0

`python scripts/check_template.py gemini`: exit 0, `conformant: gemini`.

Ran the existing `scripts/run_local_e2e.py` module's `_run_one(Path("gemini").resolve(), "")` using its normal sanitized `_child_env`, with the prepared Python and real pinned binary on PATH. This starts actual `commands.py`, waits for health, invokes actual `e2e_test.py`, and stops/cleans the server. Exit 0. Nine checks passed: health, command discovery, typed metadata, missing/mistyped argument HTTP 400, unknown command 404, read-only setup, real version 0.64.0 and missing-key HTTP 500 guard. L3 explicitly SKIP because `E2E_RUN_LLM=0`; this is local-only, not image/cloud/model acceptance.

## PASS — required-model negative check; BLOCKED — required L3

Ran the same actual local HTTP runner with sanitized child environment, changing only `E2E_REQUIRE_LLM=1` and `E2E_RUN_LLM=1`. Actual setup reported no compatible key. Nine diagnostic checks passed; `required L3 target has no compatible API key` failed and `e2e_test.py` exited 1 as required. The negative-check driver confirmed the expected failure. No model invocation occurred and no coding resources were created. Genuine `GEMINI_API_KEY` is a missing L3 prerequisite; an OpenAI key was not substituted.

## BLOCKED — image/cloud/provider acceptance

Docker is not on PATH, so no real Docker build (L1) or source-image deployment (L2) was performed. No new provider evidence JSON, `tested_on` provider or official acceptance was added. The 2026-10-14 image-build record is historical source, not current-source L1 evidence. No L4 run was attempted. Local regressions and HTTP checks do not establish these tiers.

## Remaining delivery gates

Independent cross-review, scoped repository commit/PR, required CI and verified merge remain pending at this checkpoint. Full catalog/shared CI orchestration belongs to the coordinating task. This record is not a publication or merge claim.
