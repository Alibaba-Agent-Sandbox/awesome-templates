# Verification: contributor standards and Express platform steps

Date: 2026-10-19
Result: PARTIAL

## Scope and provenance

Branch based on main `052051411a5f78743083d68467ba952a4e71e08b`. Scoped changes are
AGENTS/contribution/navigation, bilingual project/documentation/step guides,
template README step links, local Markdown checks and CI, the explicit step
materializer/batch driver, canonical build selection/READY polling, and new
dated audit/engineering/pilot records. Existing work in the original checkout
is preserved in place; this work uses an isolated worktree.

Local controller: Linux x86_64, Python 3.13, PyYAML 6.0.3, httpx 0.28.1,
pytest 9.1.1. Paired SDK source `d4d93e8cbb986f33a8868f7a4139ed0edb49eaba` was
downloaded at that immutable commit and installed into an isolated virtualenv.
The 0.3.0 release binary SHA256 is
`e6d1c46626fd3f48e86b23bc99b0b8d565dfadd3f61a42ea352a27cb637d9cdd`, checked
against its official release checksum. It uses the existing official SDK modules
through NODE_PATH; the independent published 0.4.0 uses incompatible standard
template-list/create interfaces and is not silently substituted.

## Executed local checks

- PASS: `python scripts/test_spec_tools.py` baseline: 36 tests, no failures.
- PASS: `python scripts/check_template.py --all --strict`: all 23 products plus skeleton, zero violations.
- PASS: `python -m pytest -q scripts/test_local_cleanup.py scripts/test_express_runtime_socket.py opencode/test_e2e_protocol.py`: 46 passed.
- PASS: `python -m pytest -q scripts/test_prepare_steps.py scripts/test_check_docs.py scripts/test_spec_tools.py scripts/test_express_cleanup.py`: 56 passed and 48 subtests passed.
- PASS: `python scripts/check_docs.py`: 112 current documents, zero missing targets/fragments. Historical engineering evidence remains immutable and is not rewritten by this check.
- PASS: all 24 existing Dockerfile profiles materialize with explicit source hashes and pinned server override. This is local plan validation, not 24 cloud passes.

## Real cloud pilots

All runs originate locally with existing credentials in process environments;
no credential is uploaded to Actions or committed. A RUN-only Python hello step
deployment reached official READY, created a real sandbox and passed hello and
run_script externally through both CLI and SDK (4 calls). Independent cleanup
confirmed owned sandbox/template absence.

A second successful pilot added native ENV key/value pairs, WORKDIR and USER.
It passed the same four calls and two additional external run_script assertions
that the server inherited STEP_PROBE and ran as user. See
[pilot receipt](../../../python-hello/evidence/step-pilot-2026-10-19.json).
The source-built server in these pilots is pinned separately to
`e2cb27e24fde0a67112f82b8d44af463445a5d1a`, matching existing image CI.

Failed attempts remain separate: the published standard CLI rejected the native
list options; the standalone 0.3.0 initially lacked its external official SDK;
a native CLI submitted response was correctly rejected before READY polling;
the old CLI formats status dictionaries as strings; and the real platform rejected
single-argument ENV. The corrected runner parses status safely, waits for actual
READY and uses alternating ENV arguments. These failures are not cloud passes.
Private diagnostics and exact owned recovery journals remain outside the repository.

The actual generated Python hello recipe also completed the real canonical
deploy/create/four CLI+SDK calls/independent cleanup path. Catalog-wide generated
step deployment is in progress and is not represented as complete here.
No L3/model or new Dockerfile L1 is claimed by these pilots.

## Original Issue and PR inventory

The authenticated GitHub API was paginated without author filters. At the start,
64 Issues were open and no PR was open. Current repository access permits normal
task-branch publication; main has no branch protection/ruleset, but checks/review
are still respected. The original-64 snapshot is
[machine readable](../../../docs/issue-delivery-2026-10-19.json).

Verified merged implementation and exact acceptance permitted closing Issues
84, 93, 110 and 114. The local regression results and existing merged real-model
receipts support those narrowly scoped closures. Broader template Issues remain
open until their actual deployment/product criteria hold. No synthetic directory,
provider ID conversion or unsupported product replacement is counted as completion.

## Remaining gates

The complete original roadmap, every generated template's real Express outcome,
required real-model acceptance, final current-head CI and actual PR merge remain
pending. This record does not declare the user's complete request fulfilled.
