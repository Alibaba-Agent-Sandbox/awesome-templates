# Verification: standalone Agents API Harness family

- Date: 2026-11-17
- Result: BLOCKED for release/image/cloud/model/upgrade acceptance; local scope below verified.
- Source base: ee59a726bb04e9b67a79b1bcbbb0a528ced11ef1 (PR311, open Draft).
- Changed scope: six standalone recipes, closed-source family generator, catalog, active readers/tests and bilingual consumer/contributor/design documentation.
- Runtime: actual paired editable SDK candidate, version0.4.0a8; this is not a public package installation.

## Executed validation

- `python scripts/check_template.py --all`: PASS, all current source entries plus skeleton conform; no cloud/model operations.
- `python scripts/test_spec_tools.py`: PASS,57 tests; negative fixture conformance output is expected, final unittest result OK.
- `python -m pytest -q scripts`:514PASS/4FAIL/2SKIP and220 subtests at the recorded final full-script checkpoint. The four failures are existing anonymous-RAM registry credential tests: this interpreter lacks os.memfd_create. Assertions were preserved. A later added shell regression is verified separately below.
- `python -m pytest -q scripts/test_agents_api_family.py agents-api-codex/scripts/test_release.py agents-api-codex/test_smoke.py`:35PASS/19subtests. Includes actual local role HTTP readiness/auth/drain with SQLite, original release safety cases, file/smoke checks and six standalone source/credential/admission cases.
- Actual ManagedService freezes each new Session, then actual ManagedExpressBackend.create reaches the infrastructure boundary with the exact native model allowlist. Before the fix all six rejected model_env_not_allowed; after the fix all six reach the deliberately stopped infrastructure boundary. No cloud create occurs in that regression.
- The exact Guest npm RUN shell for each Dockerfile executes against bounded stand-in commands. This catches the generated stray plus-token failure; it is not a Docker build or npm package-install claim.
- `PYTHON=<configured-venv-python> npm test --prefix contracts/template-v1`: PASS actual JS/Python schemas,11 valid/25 invalid,4 invalid registry and13/25 raw YAML fixtures. Initial npm run used system Python without jsonschema and failed; selecting the configured interpreter fixed that environment invocation.
- `python scripts/sync_agents_api_templates.py --check`, runtime runner/reference synchronization, managed-catalog and docs checks: PASS in recorded scope. Generated projects do not read sibling templates; private dotenv variants are outside the generator's closed input list.
- Initial multi-positional checker invocation was rejected; corrected to supported --all. Initial renamed-runner/catalog fixture tests failed, then were updated to actual new identities without changing preserved original migration evidence.

## Adversarial findings

First independent post-implementation review found malformed generated Docker shell, wrong model-protocol prose and a missing Session model-env allowlist. All received source fixes; the last received the six failing-before/passing-after regression. The generator now reads a closed explicit source set and checks unexpected public source files. Qoder uses the actual qoder binary and native PAT. OpenCode tool records are completion-only; no realtime per-tool deadline is claimed. Second independent reviews and final revision evidence are linked below when completed.

## Required remaining gates

PyPI metadata queries confirm latest client/server0.4.0a7 and no0.4.0a8 files at this observation. Both Dockerfiles deliberately target the new candidate; no older-runtime substitution or source fallback is used. This environment has no Docker executable, prepared existing PostgreSQL URL or FC execution-role configuration. The root dotenv and supported user configuration locations were checked without printing values; platform/model credentials exist but are not database/role inputs. User was asked for private configuration locations; no value is copied to Git.

Still required: matching runtime artifact publication, real non-root Guest/Server builds, hosted PostgreSQL/FC deployment, each native authorized model/tool/file task, retained-Session upgrade through the original Worker, SSE/cancellation/durability scope and independently confirmed owned cleanup. Generic schema/HTTP fixtures and old image/model records do not satisfy these gates. Keep Issue309 and coordinated Draft PRs open.

## Cleanup

Only local temporary projects, SQLite files and owned loopback role processes were used. Test finally blocks stop role subprocesses. No new cloud resources or management keys were created; no account-wide cleanup or resource inventory is claimed.

## Completed independent post-implementation reviews

Two additional rounds were completed after the initial three-agent analysis. The first found and corrected concrete shell, credential-admission, native tool-event and documentation defects. The second independently rechecked those corrections, caught a permissive shell-test stand-in and an OpenCode permission widening, and verified the fixes. Source design is reasonable within its declared limits; both reviewers explicitly conclude that overall release acceptance is incomplete.

Canonical cross-owner reviews: [protocol round2](https://github.com/Alibaba-Agent-Sandbox/python-sdk/blob/feat/agentsapi-harness-20261117/.agents/evidence/verify/2026-11-17-agents-api-reviews/post-round2-protocol.md), [runtime round2](https://github.com/Alibaba-Agent-Sandbox/python-sdk/blob/feat/agentsapi-harness-20261117/.agents/evidence/verify/2026-11-17-agents-api-reviews/post-round2-runtime.md). Template-specific first-round originals remain in the adjacent dated review directory. The strengthened shell regression now strictly validates argv and proves the original stray-plus control fails in all six cases.

Final active-guide inspection restored the actual per-project private `.abx/agents-api/` path after the public recipe rename; changing a public template ID must not rename its existing internal release store. The family guide owns native credential choices. Both languages were checked.

## Keyless source-contract CI

Added `Managed source contract` after independent protocol/runtime pre-analysis and a code review. Both checkouts are read-only and do not persist credentials. It installs paired editable SDK source in one resolver transaction from public commitd336eb89aa2685ead3d173103b7a6e5c964ed829, checks actual module origins/paired a8 metadata and pip consistency, then runs the family/release/smoke contracts. The local origin probe and YAML/permission checks passed. Remote job execution remains a separate gate; this never substitutes source for the Dockerfile's published-runtime dependency or certifies old Python YAML consumer migration.

Scoped configured-credential/private-endpoint scan: PASS, zero matches in this repository's changed files. Final record/doc links and whitespace checks passed.
