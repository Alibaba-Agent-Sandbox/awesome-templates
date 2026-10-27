# Explicit startup model configuration

Result: PARTIAL

Date: 2026-10-27. Scoped Qwen2.2.0/DeepSeek1.2.0/Hermes1.2.0 runtime, manifests,
bilingual README, design and regressions. Existing published CLI environment
resolver confirms nonempty declarations win over host exports.

- Existing command regressions: PASS48 (pytest --import-mode=importlib).
- Modified command regressions including new behavior: PASS51,27.20s.
- New cases against original commands: FAIL2/PASS1, reproducing Qwen's omitted
  child endpoint/model and Hermes's blank-provider setup-key mismatch. Explicit
  Qwen service settings already worked at the command layer and remain so.
- Initial combined pytest invocation without importlib failed module collection
  because three files share test_commands.py; no runtime conclusion from that error.
- python scripts/check_docs.py: PASS224 documents/zero failures.
- python scripts/check_template.py --all: PASS,zero claimed-spec failures.
- Real modified-source/native/model/documented consumers: PENDING.
- Current-head CI, separate articles and Registry review: PENDING.

No cloud/model credentials are included. Vendor fallback behavior is preserved;
no claim of native vendor account authorization follows from compatible-service use.

Actual first-source cloud findings: Qwen/DeepSeek core PASS. DeepSeek fresh CLI/SDK/HTTP
also PASS with actual second model. Qwen documentation attempts01/02 FAIL: native
init selected qwen3-coder-plus despite configured OPENAI_MODEL=qwen3.8-max, and returned
an API404 model-missing string marked success by upstream; no required file existed.
Both failures and independent cleanup are retained. Native Qwen needs an explicit
--model flag; forward per-call model or the configured/fallback startup model and
extend regression assertions to the actual argv. Fresh changed-Qwen cloud runs pending.

Qwen explicit-model argv regression: PASS13; the two new configured/default cases both FAIL against first-source113ebb1, proving missing CLI model forwarding independently of upstream requests. Removed a trailing blank line reported by diff check; no executable change.

Second actual Qwen source35f676f core PASS17, but docs03 FAIL with the same native
qwen3-coder-plus init/API404 despite forwarded CLI model selection. Remaining baked defaults identified in Dockerfile: OPENAI_MODEL/OPENAI_BASE_URL
can shadow launch settings on this prewarmed runtime; the controlled whole-image
removal is required to establish the causal correction. Remove both image ENV defaults, keep prior defaults only
in commands.py, and require actual native initialization to match selected model.
The earlier explicit-flag correction alone was insufficient; do not relabel docs03.
Fresh whole-image/native/documented verification is required for this new recipe.

## Complete scoped provider experiences

All three final experiences PASS on actual default Docker/Express. [Method audit](2026-10-27-startup-model-overrides/method-audit.json) lists every method, including each historical run compatibility command. Native core assertions: Qwen18, DeepSeek17, Hermes17 (individual receipts authoritative); no failure/skip/not-run. Real source repair, original tests preserved, independent original/held-out execution and actual reports pass.

Qwen final docs04 PASS14: literal CLI, unchanged SDK and HTTP each initialize exactly qwen3.8-max, generate fresh files/reports, and independently execute downloaded code. This follows actual qwen3.8-flash native work with the corrected image; omitted vendor fallback is separately covered by regressions. Previous three real failures remain immutable above.

DeepSeek and Hermes each complete11 fresh documented checks with actual qwen3.8-max after qwen3.8-flash core. Hermes original overall cleanup failure and new independent supplement are retained separately; original completed business is not rerun or relabeled. All own resources are independently absent.

All three supplementary compatibility runs PASS4 each: actual model-generated Python bytes uploaded to a fresh instance, run through named run via CLI/full SDK/direct HTTP, exact output, independent file and all outer/prepared/image absence. These add zero model calls and cover previously untested public compatibility methods. Every template has4 named methods now actually invoked. Exact core/docs/compat staged identities match; all runtime folders unchanged at reviewed source.

Local checks:51 command regressions; final Qwen command/controller union76 including actual-model-identity rejection. Specification39 and all-template/document checks passed earlier; no other runtime changes after those checks. Current source-head CI, separate three articles and Registry review remain pending. Full50 task is not complete.
