# Gemini and Qwen isolated coding-verifier checks — 2026-10-16

Result: PARTIAL

Scope: `gemini/e2e_test.py`, `gemini/test_e2e_protocol.py`, `qwen-code/e2e_test.py`, `qwen-code/test_e2e_protocol.py`, and this change's engineering records. Baseline repository HEAD `2acb53481739e9585803076dd4c05ce5c2048219` plus existing scoped development changes. Other template/source/CI/catalog changes are preserved and owned by coordinating work. Environment: Linux, prepared Python 3.13.13 development environment, actual isolated Gemini CLI 0.64.0 and Qwen Code 0.23.0 binaries.

## Tested verifier hashes

| File | SHA-256 |
|---|---|
| `gemini/e2e_test.py` | `66db5c4b2c90ff0ba30f9aea70efdd43c1c93ba561c34eb67bdfc2032e524f4c` |
| `gemini/test_e2e_protocol.py` | `961e84424d5c55d4694920b87729b47b709c1944dab4fe38a54acf08f26a5304` |
| `qwen-code/e2e_test.py` | `0fd1ec63d70c09325e4af17ef4c1a29be9e56b10271ec5de80c97d36f98200ec` |
| `qwen-code/test_e2e_protocol.py` | `ce03396171d2c5baa7157c9c84f80d423ae29bdba9922dca19ab3357367c923e` |

## Reproduced defect and correction

Independent OpenClaw-owner cross-review reproduced the old verifier's false pass using `unittest.py` that printed `Ran 3 tests` and source that still returned the wrong value for the original positive test while passing the former held-out values. This task changed only related verifier hunks: isolated Python startup, trusted unittest import before cwd exposure, explicit original test discovery, stronger baseline reproduction, absolute-path isolated source loading, and original-plus-held-out assertions with exact completion output.

## PASS — behavior and real subprocess negative controls

Executed with the prepared interpreter and real pinned Gemini binary on PATH:

```text
python -m pytest gemini/test_commands.py gemini/test_e2e_protocol.py qwen-code/test_commands.py qwen-code/test_e2e_protocol.py --import-mode=importlib -q
```

Exit 0: 47 passed (Gemini 24, Qwen 23). Twelve new cases execute actual verifier shell commands, covering each template's fake unittest, startup import hook, and no-shadow environments against both correct and incorrect source. Incorrect original positive input is rejected by both original-test and held-out processes. Correct code passes despite added shadow files; startup hooks never execute. Target-key and forced-off protocol controls continue to pass. These cases mock transport/model edits; they are real verifier subprocess checks, not real-model L3.

An initial combined pytest command without `--import-mode=importlib` exited 2 because both directories contain the same test filename. The corrected importlib invocation above passed; no tests or product gate were disabled.

## PASS — actual HTTP local L0 after the verifier change

Executed the existing `scripts/run_local_e2e.py` module's `_run_one` for Gemini and Qwen separately, using its normal sanitized `_child_env` and actual pinned binaries. Both actual `commands.py` servers started and their actual `e2e_test.py` exited 0: nine HTTP/diagnostic checks passed for each, including real version pin, typed metadata, precise missing/mistyped argument and unknown-command errors, setup and missing-key guard. Both printed model SKIP under `E2E_RUN_LLM=0`. Servers were stopped and runner-owned local test artifacts cleaned.

`python scripts/check_template.py gemini` and `python scripts/check_template.py qwen-code`: both exit 0, conformant. Scoped `git diff --check` passed.

## Independent OpenClaw cross-review

This task reviewed OpenClaw source/docs and ran its original 13 tests. It found an SDK `timeout` keyword collision and reproduced a real owned descendant surviving successful stop after its leader exited. The OpenClaw owner changed public parameters to `command_timeout` and retained an unreaped process-group leader through bounded group cleanup. This task reran the original real TERM-ignoring-descendant scenario: stop returned stopped and no survivor artifact appeared. After the owner's additional already-exited-leader fix using waitid WNOWAIT, this task independently reran its final 15 tests: exit 0. Both defects are corrected; no OpenClaw source was edited by this task.

## Remaining acceptance and delivery gates

The earlier [Qwen real-model run](2026-10-16-qwen-droid-verifier-cross-review.md) and [initial Gemini checks](2026-10-16-gemini-runtime.md) are preserved. They are not asserted to have executed these new verifier hashes. No real model was invoked in this new check. The coordinating task owns any subsequent real-model/Express run and its new evidence. Genuine Gemini key and Docker remain unavailable to this task; no L1/L2/L3 provider or model pass is claimed. PR/CI/merge remain coordinated delivery gates.

No root environment file or secret values were read, retained or logged. Regression fixture directories contain only synthetic source/artifacts; subprocesses completed normally and created no cloud resources.
