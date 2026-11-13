# Named resource contract: local verification

Status: PARTIAL — local source implementation; release and real image/cloud gates remain open.

## Inputs and scope

Owner branch: feat/template-v1-migration-20261112, based on
89cc3d485618a8d84a8bf16fd9f3475c688627b3. This evidence describes the working changes for
https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/311 and
https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/309, not a published package.
Python 3.13; actual JSON Schema/YAML validators from scripts/requirements-spec.txt; actual Node
contract dependencies installed through npm ci and the checked-in lockfile.

## Verified behavior

- PASS: npm test --prefix contracts/template-v1: actual schemas and JS/Python deep-equal
  normalization, 11 valid resources, 25 invalid resources, 4 invalid Registry metadata cases,
  13 valid raw YAML cases and 25 rejected YAML cases. Includes build alternatives, unknown
  references/cycles and legal post-deploy self-output references. No expressions executed.
- PASS: python scripts/test_spec_tools.py: 56 tests. Invalid synthetic fixtures intentionally
  produce checker diagnostics during the test; the suite exits zero.
- PASS: python scripts/check_template.py --all: all current source recipes and skeleton
  conform; no ignored violations.
- PASS: python scripts/check_managed_catalog.py: zero violations. Historical evidence remains
  linked without conferring new qualification.
- PASS: python scripts/check_docs.py: both-language local Markdown links/anchors.
- PASS: standalone runner regressions verify explicit creation-before-start, only allowlisted
  runtime values, generated token secrecy and 0600 file mode, no overwrite before cloud I/O,
  authenticated discovery and owned cleanup failure state. These use fake SDK transports.
- PASS: published agent-sandbox-client 0.4.0a7 wheel source inspection confirmed the exact
  create(envs, on_created), start_server(env, command, token, wait, timeout), kill_by_id and
  close signatures used by standalone scripts. Wheel SHA256:
  c5f981545bb9266663f47e8ca3ce02a48a2259125b0ffd44c575973e3205482a.

## Corrections and remaining validation

Initial expanded scripts runs exposed obsolete managed-catalog projection, native-step
fixtures, dynamic services admission tests and prepared-image launch assumptions. These
failures were retained in the local task transcript and corrected against the new contract;
they were not treated as cloud failures or removed to manufacture release qualification.
The final expanded-suite result is appended below after execution.

## Boundaries and cleanup

No cloud, container or model operation was performed by this owner's checks. No cloud
resources therefore require cleanup. Test subprocesses and fixtures use temporary directories.
A valid resource/source build plan is not evidence of real FC component invocation, image
construction/push, native template readiness or end-to-end business operation. Full required
CI/image/provider/release acceptance, actual consumer source locks and the updated CLI CI pin
must be completed separately. Historical receipts are unchanged.

## Final local run

- PASS: `python -m pytest -q scripts`: 514 passed, 2 skipped, 199 subtests passed.
  The two skips require an explicit ABX executable; both were then run separately with
  the matching built CLI source and passed. That check uses an empty temporary home and
  no cloud credentials; it verifies actual parser/help dispatch, not cloud operations.
- PASS: `python scripts/test_spec_tools.py`: 56 tests after the final managed startup correction.
- PASS: template and managed catalog checkers, Markdown link check, generated field reference,
  generated standalone runtime scripts, 15 canonical process helpers, 8 controller ownership
  copies, and `git diff --check` after the final source edits.
- PASS: 92 focused runtime/HTTP/receipt/reference regressions (plus 6 subtests), including
  preserving cloud cleanup state when local transport closure fails.
- Managed classification now reads actual native Serving environment/role declarations.
  Its local test runner uses an owner-maintained fixed business entry; arbitrary native
  template snapshot commands cannot become host process arguments. Managed production
  startup stays in the existing SDK backend after dynamic creation and credential injection.
- Both prepared-image and public-source engineering harnesses now use template-owned
  runtime startup. The public-source harness compares the deployed manifest and runner
  bytes against the verifier source before calling the application. Retained owned images
  remain PARTIAL cleanup, rather than being silently treated as deleted.

The full scripts suite was initially blocked at collection by missing optional SDK/aiohttp
packages in the isolated test environment; installing the exact SDK/server 0.4.0a7 and
httpx 0.28.1 plus aiohttp 3.13.2 enabled that expanded run. No repository dependency lock
was rewritten. A mistyped focused-test filename was corrected before the successful run.

Final classification-only follow-up: 20 application/managed/migration tests and 4 subtests
passed after confirming that deferred native environment values are not treated as business
classification data. The public schema and shared normalizers were unchanged by this follow-up.
