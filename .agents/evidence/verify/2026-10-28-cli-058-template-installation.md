# Verification: CLI 0.5.8 template installation guidance

- Date: 2026-10-28
- Result: PASS for scoped local documentation and independent public-package availability; remote CI/review remains required.
- Scope: two shared installation guides, accepted README decision lifecycle and new records.
- README source change: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/289,
  MERGED at 2026-10-28T03:36:09Z, commit 7a18170957942d18195f193efac543a6259d1231.
- Default-branch README readback confirms the reported internal acceptance paragraph and receipt
  links are absent; all source/managed entries remain available.
- CLI source: https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/pull/208 (MERGED).
- Public stable release: https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/releases/tag/v0.5.8.
- Fresh official exact-version npm metadata returned HTTP 200 for 0.5.8 after initial propagation 404s.
- `python3 scripts/check_docs.py docs/using-templates.md docs/using-templates.zh-CN.md`: PASS.
- Python client remains 0.4.0a6. No catalog, manifest, runtime or previous evidence changed.
- No cloud resources were created by this docs update. Runtime release checks belong to the CLI owner.

- CLI owner independently installed official npm 0.5.8, passed artifact checks and exercised real
  authenticated application-token generation/reuse with independent HTTP 404 cleanup.
- CLI publication evidence: https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/pull/208;
  the new publication record is delivered in its separate documentation follow-up.
- `git diff --check`: PASS; scoped Markdown links: six documents, zero failures.
