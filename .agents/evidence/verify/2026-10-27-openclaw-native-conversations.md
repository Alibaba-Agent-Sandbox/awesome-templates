# OpenClaw native conversations

Result: PARTIAL (implementation and local checks only; actual native run pending)

Date: 2026-10-27. Base80167d7. Existing Docker/native versions unchanged.
- pytest openclaw/test_commands.py: PASS40, including explicit partial/invalid
  model config, same-session routing, redacted HTTP failures and existing ownership.
- check_template.py openclaw: PASS; check_docs.py: PASS.
- Native provider/model/full documented consumers: pending. No provider qualification.
- Source is an isolated task worktree; no unrelated workspace changes included.
