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
