# Unified launch release documentation verification

Status: PASS for local documentation, preserved matrix receipts and the confirmed public release checks below. Final PR merge remains governed by current-head CI.

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

## Managed catalog release gate

The coordinating public catalog experiment found that CLI 0.5.0 only read source rows under `templates`, while the actual catalog stores native managed entries under `managed_templates`. Bare-name `base` resolution failed before creating a cloud resource. This does not invalidate the recorded 46 source-recipe launches, but CLI 0.5.0 is insufficient for the full current catalog.

Current installation guidance and all managed quick starts therefore target CLI 0.5.1. The initial documentation amendment was held until publication and a successful public managed-catalog launch were confirmed. The earlier successful CLI 0.5.0 installation remains a historical fact. No cloud matrix is repeated for this prose update.

The CLI owner tracks the fixed candidate and its separate real `base` lifecycle evidence in [PR 154](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/pull/154). The initial documentation amendment passed the 222-document link check and whitespace check; the public-release gate is completed below.


## Public CLI 0.5.1 release and base launch

The release coordinator confirmed the following executed checks on 2026-10-25, separately from the source-candidate OpenSandbox matrix:

- PASS: [binary workflow 40184565506](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/actions/runs/40184565506) and [npm workflow 40184777604](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/actions/runs/40184777604).
- PASS: [release v0.5.1](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/releases/tag/v0.5.1), source commit `8b4d9ad1ebf8b1329039bc292a3fe0ac1a32784f`. The release has 12 assets. Package archive SHA-256 is `3c5bac30cedcb48ecea5b34d9ee3fcb43d2fb069ebff6c54a6bd5ce162ad1efa`; archive/sidecar SHA-256 and npm SHA-512 integrity checks passed.
- PASS: fresh official npm installation using an empty cache and npmrc, followed by artifact smoke checks. This documentation reviewer independently read official npm version and `latest` metadata; both resolve to 0.5.1. The release tag's annotated Git object resolves to the exact commit above.
- PASS: real Express `template launch base` through the default public Git catalog, sandbox lifetime 300 seconds, shell execution returning `42`, `kill --yes`, independent GET returning 404 and final reconciliation finding no owned resources.

Python client/server 0.4.0a1 official PyPI installation was separately confirmed by the release coordinator. The successful public `base` test does not certify the other three managed templates, native interpreter/desktop interfaces, model tasks or PTY. Their historical receipts retain their original versions and call paths. The 46-source matrix still records its original source-candidate revisions; it has not been relabeled as a public CLI 0.5.1 matrix.
