# Verification: template v1 source migration

Date: 2026-11-12. Producer base: `6dfaf3990b43364ea8ec1e2f5a46dc4db2cc0811`.
Tracker: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/309.
Result: PARTIAL — local migration checks pass; image/cloud/model/release gates remain separate.

## Source and scope

- 48 root v1 resources,47 source publication descriptors, four original native managed
  references with their own documentation metadata. Native entries remain noninstallable.
- Original48 declarations are preserved under scripts/fixtures/migrations. Smoke/priority/wave
  are engineering inputs. All48 root Dockerfiles, commands.py and e2e_test.py are unchanged; only the separately declared Managed Server image recipe changes its client source.
- SDK launch contract source is exactly ab50ad8e750b15221c25ccf231caffdc3f196983, copied by the
  committed-byte verifier; old schema files/records remain historical, not accepted public input.
- Python3.13.13, Node22.22.2, actual AJV8.18.0/jsonschema4.26.0. Local HTTP checks use published
  client/server0.4.0a7 only for their unchanged connection/bridge surface. Development CLI tests
  exercise the current built source tree, not a claimed released artifact.

## Local verification

| Check | Result and scope |
| --- | --- |
| Canonical JS/Python schema and compile vectors | PASS:21 positive,58 negative resource and9 negative metadata cases; outputs agree. |
| Canonical Python suite | PASS:12 tests. |
| Static root template checker | PASS: all48, zero claimed spec failures. |
| Native managed catalog checker | PASS: four entries; historical proof remains historical. |
| SDK generic launch source lock | PASS: exact committed input bytes and v1 schema correspondence. |
| Bilingual field reference generator --check | PASS; no native variable evaluation. |
| Markdown link checker | PASS:238 current documents, zero local failures. |
| Original workload migration regressions | PASS:3 checks cover all48 workloads/engineering declarations,47 publication locators and both-language declared configuration names. |
| Complete scripts suite with source CLI | PASS:475 tests including the real source CLI parser/help, static expression regression, migration invariants and local transport/cleanup checks. |
| Required direct spec-tools suite | PASS:59 tests including the static numeric-expression regression; intentional invalid fixture diagnostics and child timeouts are expected assertions. |
| Source CLI parser/help | PASS:2 actual no-cloud tests; neither was skipped in the full source-CLI run. |
| Selected original local controllers | PASS:_skeleton, python-hello and agents-api. Python-hello retains20 actual HTTP/file/script tests; Managed bridge checks readiness, private authentication and closed route surface. |
| Official immutable SDK source client build/install | PASS: client[managed-agents] from1079841307f1f63253ae68fdda6e6d2d1e77e851, archive SHA256a7dfffac2eba7a8ee3d5620d231c5abf3f767ca655194b7329341389faf83485; new ManagedConfig/Worker env/literal-v1 ports assertions and pip check pass. This is not a PyPI release or Docker build. |
| Scoped Ruff and git diff --check | PASS after correcting new-source imports/executable mode and whitespace. |

## Corrected failures and limits

Initial scripts runs exposed old-format test fixtures, a prepared-reference carrying invalid
preparation props, and legacy raw-port loss. They were corrected with active regressions,
retaining the original workload and cleanup assertions. The original full run used a
Python3.11 environment without os.memfd_create; a pinned Python3.13 environment runs the
RAM-only checks without weakening or skipping them. An unscoped local runner invocation
without the intended process PATH failed missing runtime imports; it confers no acceptance.
Corrected scoped controllers use the active environment and their original tests.

No full upstream-tool local matrix, Docker image build, native steps registration, real cloud
deployment, model turns, revision upgrade/drain, remote cleanup, npm/PyPI release or public
catalog activation is claimed. No cloud resources were created. The obsolete bindings and
example toolchain files are retained only under engineering fixtures/Git history.

The actual installed source provenance and bounded import/model checks are recorded in
[managed-source-client.json](2026-11-12-managed-source-client.json). Only the Managed Server
Dockerfile changes its client input; the Guest and other source image recipes retain their
existing published dependencies. No image/cloud pass is inferred from host pip installation.
