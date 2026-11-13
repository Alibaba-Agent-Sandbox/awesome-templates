# Verification: v1 source-reader consumers and final SDK source dependency

Date: 2026-11-12. Parent migration commit: 59e5b75. Canonical producer:
ef695803cb78bf82b8473195fcb37b3e6357a363. Tracker:
https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/309.

- PASS: complete scripts suite516 tests, zero skips, Python3.13.13 with source CLI.
  Includes39 actual source-file regressions: shared13 valid/25 invalid cases, plus actual
  checker/metadata/catalog on/date preservation and no process-environment interpretation.
- PASS: direct specification suite59; all48 source resource checks; all4 native declarations;
  238-document link check and generated field reference --check.
- PASS: final immutable SDK b988 archive fresh wheel build/install with managed-agents extras,
  exact direct_url/archive provenance, actual ManagedConfig/Worker/TTL/port helper probes,
  actual installed reader13 valid/25 invalid vectors and pip check. See
  [source provenance](2026-11-12-managed-source-client-api-reader.json). Distribution metadata
  remains0.4.0a7; this is source installation evidence, not publication.
- PASS: scoped Ruff unused-import checks and git diff whitespace checks.
- Preserved: previous c550 Server and unchanged Guest real image evidence in
  [local image baseline](2026-11-12-agents-api-local-images.json). That receipt does not cover
  the final SDK Session API projection. Final Server Dockerfile is frozen at SHA256
  f13427c5c0bac4f04799775823f0c1ed09e35bfe26d8ceed4a566b3a52c16145 for the independent
  runtime-owner rebuild. No image was built by this owner increment, and no cloud/model
  execution or resource creation occurred in these checks.

Commands: `python -m pytest -q scripts`, `python scripts/test_spec_tools.py`,
`python scripts/check_template.py --all`, `python scripts/check_managed_catalog.py`,
`python scripts/check_docs.py`, `python scripts/sync_template_reference.py --check`,
scoped `ruff check --select F`, `git diff --check`, and fresh SDK `python -m pip check`.
Source-reader regressions are included in the v1 CI specification job; native expression
resolution remains the CLI official-parser phase, not this source reader.

## Stacked branch ancestry closure

The pre-merge `git merge-tree --write-tree ef695803cb78bf82b8473195fcb37b3e6357a363
f9c8391ca9f1c47fc328597ebea5b08ffec7cc58` reported exactly one conflict:
.agents/README.md. The common ancestor was6dfaf3990b43364ea8ec1e2f5a46dc4db2cc0811.
The migration tree already contained the exact canonical contracts/template-v1 directory,
two public schemas and requirements-spec bytes; their diff against ef695 was empty.

A normal non-fast-forward merge brings the actual canonical ancestor into the migration
branch. Keep the migration record index, which contains all canonical entries and the
additional owner migration/reference/image/consumer entries. No product file or Server
recipe changes are needed. Server Dockerfile SHA256 remains f13427c5c0bac4f04799775823f0c1ed09e35bfe26d8ceed4a566b3a52c16145.

PASS after conflict resolution: directspec59, source48, native4, docs238, generator drift,
Python canonical14 and actual Node/Python deep-equal vectors21 positive/59 resource-negative/
9 metadata-negative/13 YAML-positive/25 YAML-negative. `npm test` initially selected the host
Python without jsonschema and failed before assertions; rerun with the documented dependency
venv first in PATH passed. This environment failure is preserved separately from product
results. Full516 owner scripts passed at the pre-merge identical product tree, so this
ancestry/record-only merge does not repeat image, cloud or model matrices. Remote mergeability
must be rechecked after the parent pushes the new merge head; local merge is not remote proof.
