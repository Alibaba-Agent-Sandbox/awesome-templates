# Verification: persistent controlled managed business-check reports

- Date: 2026-11-06
- Change: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/295 and https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/296.
- Result: PASS for local report and failure/cleanup behavior; new template0.1.3 cloud/model acceptance remains pending.
- Baseline: template commit `185e9890b575278093a8d90a94e2c63b10e15b58`; public CLI0.5.9 and matching Python0.4.0a7 pins remain unchanged.
- Environment: Linux, CPython3.12.13, httpx0.28.1; local filesystem and owned loopback HTTP only. No model/provider credentials are used by these regressions.

## Problem and scope

A normal public Qwen deployment passes its39 positive operations,38 authentication checks, stream and active-cancel checks. The subsequent public Codex update stops at `candidate-smoke`. The original smoke catches and discards its controlled failure label, while the CLI removes its temporary hook context/result. The exact original failure cause cannot be reconstructed from those generic results. It remains a failed update, not a known model, protocol or timing root cause.

The change is template-local reporting. It does not alter the CLI, shared runtime, HTTP API, hook result protocol, model prompts, business assertions or budgets. Version0.1.3 records running progress before HTTP work in a private report directory derived only from the trusted script's template root. Each attempt has a fresh append-only JSONL file, bounded to128 rows and64KiB, plus an atomic latest snapshot. Paths do not depend on CWD, request URLs or arbitrary hook context fields. Reports remain outside the temporary hook directory.

Only finite phases/check codes, an actual numeric HTTP status, known terminal enums and cleanup booleans may be serialized. Unknown exceptions become `unexpected_error`; no exception string, hook/operation/resource identity, URL, model text or credential is retained. Failed report writes cannot return success or skip known cleanup. A running last checkpoint after termination is not completion or independent provider absence.

## Executed validation

```bash
python -m pytest agents-api/test_smoke.py -q
python scripts/test_spec_tools.py
python scripts/check_template.py --all
python scripts/check_docs.py
```

The focused run preserves every original smoke regression and adds persistent-success/failure, real HTTP503, safe transport/unknown/terminal classification, previous-history preservation, temporary-hook deletion, bounded writes, symlink refusal, report I/O failure and cleanup-order cases. A real source-controlled subprocess is SIGKILLed after fsync of its running summary checkpoint; its last phase remains readable and no success is invented. The loopback server observes a persisted running checkpoint before the first request. Its sensitive response body and test credential never enter the report or child output.

| Check | Actual result |
| --- | --- |
| Existing and new smoke regressions | 20 passed in 1.14s |
| Specification/tool suite | 52 tests, OK |
| Complete manifest checker | 48 conformant templates; 0 claimed specification failures |
| Markdown links | 232 documents; 0 failures |
| `git diff --check` | Passed |

The specification suite includes intentionally rejected fixtures and deliberately terminated process groups; its final result is `OK`. The final smoke source SHA-256 is `4cd38fc6f25b989068f1f16e48c75603bdc1cf92cbe81dffc96950dc4a48e4be`. The repository's existing `agents-api/test_smoke.py` CI entry runs all 20 smoke cases. The report's initializer and final close errors produce only the static `report_io` warning and a nonzero command result. No new cloud acceptance is claimed by these local regressions.

## Cleanup and limitations

All loopback servers, threads and owned subprocesses terminate; pytest removes its temporary report trees. No cloud resource was created or changed. The reporter's `cleanup_confirmed` covers only known cleanup actions in this smoke; it does not certify unknown mutation outcomes or provider-wide absence. The original failed public update, its source snapshot and cleanup evidence remain separate. Fresh public Codex, upgrade and final resource-cleanup gates remain required.
