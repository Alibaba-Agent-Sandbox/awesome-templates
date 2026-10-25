# Unified launch release documentation verification

Status: PARTIAL — local checks and public package availability confirmed; follow-up PR gates remain pending.

## Scope

Prepared from template PR head `ecf15959e2620402d6d497b1378e00c39a16fc78`; delivery base is merged main `45eb6c40b8d40e8ae1799420631cec1f5cb2f832`. Branch: `docs/unified-launch-release-evidence`. Changes are installation prose/commands, managed guide prerequisites, the catalog's explanatory comment, dated README/index summaries and new immutable evidence. No template manifest, runtime recipe or historical receipt changes.

The [complete source-candidate matrix](2026-10-25-unified-launch-opensandbox-matrix.md) preserves 46 existing receipts, 73 smoke definitions and 219 CLI/Python/HTTP calls. Saving and inspecting those artifacts does not launch new resources. The original matrix's independent cleanup remains recorded in each receipt.

## Validation

Executed locally with Python 3.13 and the pinned checker dependencies:

- PASS: `python scripts/check_docs.py` — 222 current documents, zero failures.
- PASS: explicit link checks for `.agents/README.md` and the three new Markdown records — four documents, zero failures.
- PASS: `python scripts/test_spec_tools.py` — 58 tests. Synthetic failure-path output belongs to unit fixtures and is not cloud execution.
- PASS: `python scripts/check_template.py --all` — 47 source/skeleton directories, zero failures.
- PASS: `python scripts/check_managed_catalog.py` — zero violations across four entries.
- PASS: the preserved matrix's offline verifier — 46 receipts and manifest hashes, 73 smoke definitions, 219 consumer calls, exact source pins and independent cleanup.
- PASS: all 48 copied JSON files (46 receipts, index and verification summary) are byte-identical to the downloaded/verified files.
- PASS: `git diff --check`.
- PASS: independent HTTPS metadata reads from official npm and PyPI confirmed CLI 0.5.0 and client/server 0.4.0a1 version records.

The initial new offline verifier incorrectly assumed every smoke had a literal `expect`. Inspection confirmed 67 explicit-result smoke definitions and six nonempty-result definitions. The verifier now checks that each receipt agrees with its manifest; all 73 pass. The documentation records this distinction. No manifest or original receipt was changed.

The coordinating release owner confirmed fresh official-registry installation of CLI 0.5.0 and both Python 0.4.0a1 packages. CLI [publish run 40181040899](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/actions/runs/40181040899) succeeded, and [template PR 213](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/213) merged at the delivery base above. Documentation explicitly uses the official npm and PyPI registry URLs to avoid stale mirror metadata. These package-installation facts do not turn the earlier source matrix into a published-package cloud experiment.

The follow-up PR still requires current-head CI and review before merge.
