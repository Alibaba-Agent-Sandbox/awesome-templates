# Express steps verification checkpoint

Result: PARTIAL.16 of23 existing source templates have genuine passing canonical
steps receipts at this checkpoint; Kimi is delivered separately in PR122. Every
listed pass required real build/official READY, CLI + SDK named commands and
independently confirmed owned sandbox/template cleanup. The [receipt index](2026-10-19-steps-checkpoint-1555.json)
contains immutable per-receipt SHA256. Model acceptance is a separate tier.

New passes: [OpenCode](../../../opencode/evidence/express-2026-10-19.json) and
[Qwen](../../../qwen-code/evidence/express-2026-10-19.json). Original failed and
timeout attempts remain separate records, including browser per-RUN deadline
failures. Remaining templates are not certified by this checkpoint.

Fresh scoped defect audit: Amp + canonical cleanup41 tests/18 subtests PASS.
Amp/Droid/Gemini/Qwen process tests55 PASS/1 SKIP; all same-name test files were
run with pytest importlib mode after default collection reported module-name
collisions. Current command hashes match each of the four real steps receipts.
The skipped optional test is not a model/provider pass. Issues83/90 scope is
fulfilled by merged source/regressions; separate model gates stay recorded.
