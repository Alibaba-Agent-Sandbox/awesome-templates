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
