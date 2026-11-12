# Verification: readable field reference and author-directory closure

Date: 2026-11-12. Migration parent: d1ad99146c6f52c7c7175cc3478bcad745b3ff39.
Canonical producer: fad843f60881b405cb386537337817e5144892bc.
Tracker: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/309.

- PASS: bilingual reference tests cover all189 actual property definitions (114 distinct field
  names), every nested object/type link, conditional Provider fields and generated defaults.
  The longest English table row is302 characters; no parent row embeds schema JSON.
- PASS: generator --check and238-document local link check.
- PASS: direct specification suite59 tests; original48 workload migration invariants and
  resource/catalog checks. Only the skeleton's resource name changes to example; engineering
  directory/name-based exemptions are now properly separated.
- PASS: actual final SDK source c550 official archive wheel installation, ManagedConfig instance
  and Worker environment fields, single TTL, raw-port union and entry-module checks plus pip
  check. Archive SHA256e5c8c5b1d4deef7a49f720a4e42cfca709652551fc379e1f7b1f7dec00e1afe9.
  See [final installed source provenance](2026-11-12-managed-source-client-final.json).
- PASS: scoped Ruff and git diff whitespace checks.
- PASS: complete scripts suite477 tests with source CLI, zero skips.
- PASS: independent runtime-owner real local Server and Guest builds and offline container
  probes, recorded in [image verification](2026-11-12-agents-api-local-images.json). Server
  source/Dockerfile hashes match this frozen recipe. Guest build used archived c5549a8 and
  unchanged COPY/Dockerfile inputs; it is not a current-source qualification receipt. Native
  infrastructure mapping used an in-process fixture, and no Agent/model/cloud task ran.
- Cloud/model and reader-parity work remain separate. The Server Dockerfile is frozen for the runtime owner's
  independent image build and is not changed during that build.

Commands: `python scripts/sync_template_reference.py --check`,
`python -m pytest scripts/test_template_reference.py scripts/test_template_v1_migration.py`,
`python scripts/test_spec_tools.py`, `python scripts/check_template.py --all`,
`python scripts/check_docs.py`, and the complete `python -m pytest scripts` with the built
source CLI supplied through ABX. Source install/model probes use a separate Python3.13 venv.
