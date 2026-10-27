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
- [Actual fixed public core](2026-10-27-next-app-readable-toolchain/fixed-public-core.json):
  PASS, default Docker/Express with source d594f27a0812ee40a0e548bc3e729c5adad50e4c.
  All seven methods and actual Next/Vite preview lifecycles, versions, negatives
  and cleanup passed, zero skip/not-run. All owned cloud/prepared artifacts absent.
- [Complete documented/browser use](2026-10-27-next-app-readable-toolchain/complete-browser-docs.json):
  PASS,10 grouped checks. Literal CLI scaffold/start/status/log/stop and project
  deletion; complete unchanged SDK with a read-only external-page observer; direct
  HTTP Next/Vite flows; actual external3000/5173 pages. Chrome145.0.7632.6 via
  Playwright1.58.0 showed original DOM and edited monthly-expenses DOM through HMR
  without a manual reload. Both actual screenshots retained. Vite used the exact
  SDK-forwarded hostname as allowed_host, never a wildcard.
- [Original permission failure](2026-10-27-next-app-readable-toolchain/original-permission-failure.json)
  retained. Three browser attempts failed operator cleanup assertions, preserved
  separately: connect() alone returns success/EOF on this host without an owned
  listener; a port can name an unrelated listener; /proc/net/tcp6 is unavailable.
  Corrected readback binds original owned socket inode identity in /proc/net/tcp,
  with explicit IPv4 loopback binding. Both owned listener identities independently
  absent and runner site counts0. No unrelated listener was removed. Every attempt's
  own cloud sandbox/prepared images/template was independently absent.
- Later footer-only bilingual prose now explains the working browser/HMR path.
  [Document review](2026-10-27-next-app-readable-toolchain/documentation-only-review.json)
  proves all runnable blocks unchanged from d594f27; runtime/manifest/controller
  bytes unchanged. This does not claim deployment of a changed runtime.
- Source current-head CI, article and Registry review remain separate gates.
