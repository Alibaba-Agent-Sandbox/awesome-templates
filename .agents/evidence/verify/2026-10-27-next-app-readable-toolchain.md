# Next preview public toolchain permissions

Result: PARTIAL

Date: 2026-10-27. Actual standalone CLI0.5.7, client/server0.4.0a6,
Docker29.9.2 overlay2. The original default1.1.2 failed twice at the first CLI
command: E3000 / PermissionError reading /opt/next-app/package.json. All own
sandbox/template/image resources were independently confirmed absent. Original
receipts are retained separately; the operator's restrictive source umask was077.

- Explicit actual Docker regression: inputs package.json/package-lock.json and
  command/lifecycle sources copied0600, real recipe built with the resolved
  default base. Old recipe fails actual non-root import/version inspection
  (pytest exit1). Fixed recipe passes the same check (pytest exit0,1 test), exact
  Next16.4.2/React19.3.1/ReactDOM19.3.1/Vite8.3.4. Both nonce-owned image tags were
  independently absent afterward. No source test was substituted for the image.
- Invocation: NEXT_APP_TEST_BASE_IMAGE='<resolved default base>' python -m pytest
  -q next-app/test_image_permissions.py. This optional integration regression
  skips when no explicit base is provided; that skip does not establish a pass.
- python scripts/check_template.py next-app: PASS, conformant.
- python scripts/check_docs.py: PASS,224 documents/zero failures.
- Initial local command suite:4 failed/10 passed because lockfile dependencies
  were not installed in this new worktree. After npm ci --ignore-scripts
  --no-audit --no-fund, the exact suite passed14 tests in11.34 seconds.
  The task-owned node_modules tree was then removed to recover limited disk.
- git diff --check: PASS.
- Current changed-source Express/default-Docker preview, full literal CLI/SDK/HTTP,
  docs checks and CI pending. No current provider qualification is claimed yet.
