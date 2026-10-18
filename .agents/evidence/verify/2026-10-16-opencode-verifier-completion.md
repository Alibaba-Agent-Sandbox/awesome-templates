# OpenCode verifier completion — 2026-10-16

Result: PARTIAL. Base a361f490555ead0ff67081ffb4874abf292a1b2f; only HTTP
controller/tests, bilingual/design docs and repository records change.

- PASS reproduction: actual Python subprocess loads incorrect calc.py that returns
  the expected three original cases but exits zero after printing INDEPENDENT_OK
  when called through -c. Legacy held-out process returns zero with the exact
  static marker before its assertions execute. No model/cloud was used.
- PASS initial corrected existing regressions: `python -m pytest -q
  opencode/test_e2e_protocol.py opencode/test_commands.py`, 24 passed in4.45s.
- PASS extended final suite: same command, 35 passed in6.05s. Synthetic remote
  HTTP/model uses actual shlex/direct-exec subprocesses, genuine source files and
  complete unittest modules. Added modes cover static sys.exit/os._exit, zero-test
  exit with fake test-count text, all original cases skipped, and a stale
  UNCHECKED_HASH cache whose legacy import first proves it loads the old good code.
  The corrected controller compiles actual bytes and rejects that wrong source.
  Six additional isolated verifier checks cover valid code with unittest and
  sitecustomize shadows; the startup side-effect file is never created.
- Normal CI, strict/document checks and hardened actual-image/model recheck are
  recorded separately after execution. No provider/canonical pass is claimed.

Product runtime files, template config, catalog and tested_on are unchanged.
Canonical scripts/express_e2e.py / abx template deploy is NOT RUN. Earlier genuine
model evidence predates the guard and remains immutable. Decision stays proposed;
PR remains draft while required gates are incomplete.

PASS: strict OpenCode checker;20 relative links; scoped Python AST and configured-secret scan; whitespace; all four runtime/configuration files byte-identical to parent. Independent read-only peer review found no blocker and confirmed the exact-session contract is preserved; no additional tests were claimed by that review.
