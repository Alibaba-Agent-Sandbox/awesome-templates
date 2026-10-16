# agents-cli real diagnostics and restricted API verification

Date: 2026-10-16
Result: PARTIAL

## Scope and environment

Reviewed and completed uncommitted `agents-cli/` migration, new
`docs/design/agents-cli.md`, and the owner note/evidence. Existing catalog, CI,
other-template and repository-process work was preserved. Base HEAD:
`2acb53481739e9585803076dd4c05ce5c2048219`. Refs
[Issue #25](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/25).

Linux x86_64, Python 3.13.13, agent-sandbox-server 0.3.0 built from the current local
server tree, pytest 9.1.1/httpx 0.28.1/PyYAML 6.0.3. Actual Codex 0.162.1 and Qwen 0.23.0
from the integration owner's pinned temporary CLI installation were on PATH for
real diagnostic runs. Protocol tests select their synthetic executables explicitly
on child PATH. All HTTP targets use unique temporary ports; protected targets use
fresh random synthetic tokens. No genuine model credential was injected or read.

## Findings and corrections

- Removed the previous e2e assumption that E2E_RUN_LLM=0 silently selects fake CLIs.
  Actual diagnostics now fail if a binary is missing/wrong; fixtures remain explicit
  test inputs and are not copied into Docker images.
- Fixed real import/startup failure: ServerPolicy.from_file expects a string;
  passing Path raised AttributeError before HTTP readiness. The import and both
  startup forms now work with the supported string path.
- Canonical serve resolves policy separately from module import. Template start_cmd
  explicitly passes the shipped policy, so the direct mode's restricted policy
  cannot disappear in canonical deployment. Tests derive canonical argv from the
  actual template.yaml and remove inherited policy environment variables.
- Added required v2 bilingual README and design. Images, model execution and
  provider status remain unverified instead of being inferred from documentation.

## Executed checks

- PASS: `python -m pytest --import-mode=importlib -q agents-cli/test_protocol.py`,
  exit 0, 10 passed. Actual HTTP/CLI-subprocess protocol tests cover both startup
  forms, missing/wrong/correct server token, disabled shell/files/process/model/
  additional Agents routes, both adapters with two sequential turns each,
  E2E_RUN_LLM=0 preserving PATH and missing-CLI refusal, plus output/argv privacy
  for nonzero/wrong-version/timeout diagnostics. Synthetic adapter turns are not
  actual upstream CLI/model acceptance.
- PASS: `python scripts/check_template.py agents-cli`, exit 0, conformant.
- PASS: existing `scripts/run_local_e2e.py::_run_one(Path("agents-cli").resolve(), "")`
  with ordinary sanitized child environment and real pins on PATH: exit 0/pass,
  18 HTTP/diagnostic checks; model/coding explicitly SKIP. Both versions were
  actually executed and matched; sessions were created/read/listed without turns.
- PASS: independent real-CLI authenticated HTTP suite for both direct and canonical
  startup. Canonical argv was derived from template.yaml with local path/port
  substitution only. Actual e2e_test.py exited 0 with 19 PASS for each mode, including
  missing-token 401. No model turn was submitted.
- PASS of negative guard, not L3: repeated actual e2e against both authenticated
  modes with E2E_REQUIRE_LLM=1. Each exited 1 and reported no L3 pass without an
  out-of-band artifact verifier; the driver asserted both expected failures.
- PASS: scoped diff whitespace and relative Markdown-link checks (exit 0).

## Earlier failures

Initial protocol tests failed because of the real Path policy import error;
corrected implementation passed. A test URL concatenation typo produced InvalidURL
and was corrected without changing product behavior. The initial README checker
required an explicit POST indication in curl examples; adding --request POST
resolved both language violations. An attempted duplicate CLI installation failed
with ENOSPC; only its incomplete package scopes were removed, and all validation
used the integration owner's already completed pinned installation. These failed
attempts are not acceptance passes.

## Outstanding gates and cleanup

L1 BLOCKED: no Docker executable/engine image build was run. L2 BLOCKED by the
image-build prerequisite; no provider/template pass file was added, tested_on stays
empty and no verified provider is listed. L3 NOT PASSED: this restricted HTTP smoke
has no independent out-of-band artifact verifier and submitted no genuine model
turn. Real coding acceptance must modify existing source, create an artifact and
pass independent tests; event 202 or fixture output cannot prove it. L4 NOT RUN.
Full-repository shared CI/catalog reconciliation, owner PR/review/checks and
verified merge remain integration requirements.

All owned HTTP server processes were terminated/reaped; fixture turns had
completed before shutdown. Sessions were process-local, no cloud resources were
created and no secrets/raw private output were written. No commit, push or remote
publication is claimed by this scoped review.

## Tested source hashes

| File | SHA256 |
|---|---|
| `agents-cli/commands.py` | `58bf1f93f54c53ae1992431b09502e2c5f8a5b820016a993241ab6979bef35bf` |
| `agents-cli/e2e_test.py` | `2f356e539c2c8c43a81dc958a1c9a9bc280c22fc2bc1465c0a1b97e0a588703b` |
| `agents-cli/test_protocol.py` | `fb8a175336456e58562bc254f3103ac2fc129894d3a299335d3e306f8a1cdeb9` |
| `agents-cli/server-policy.json` | `4a7f79435940b0d952c5fb0dba6ee049197bdc412a76a201b371efac9290a996` |
| `agents-cli/template.yaml` | `bae88b379d3497607e3bb82cb14d2375a1fab38c6a5b2d6b37437d9d249321fc` |
