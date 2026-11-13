# Decision: Retain awesome-templates Agents API delivery operations

Status: proposed

## Problem

The cross-repository delivery plan, remaining cloud sequence and some reproduction sources existed only in a workspace artifact directory. A standalone template checkout must retain the necessary operations and their evidence without relying on that directory.

## Decision

This is the orchestration record for delivery309. Implementation and checks stay with each owner; this file coordinates their order and links their canonical records. Keep temporary captures as supplemental originals, never the only source of required steps. Store new execution summaries, exact revisions, commands, failures, skipped/blocked cases and owned cleanup under this repository's `.agents/evidence/verify/`. Do not copy credentials or raw model/provider logs.

The inactive canonical contract landed in PR310 at merge52f7653bda0b6c6406207e28095ee09a87cb5018. The active v1 migration remains PR311. Source installation, an image check, a model task, cloud acceptance and publication are separate outcomes.

## API Design

No product change in this record-placement follow-up. Public configuration remains one local template.yaml, with optional registry.yaml for publication/initialization. Generic Serving execution/actions/flow and standalone SEA parser validation are not established by the Managed path.

### Owner operations already available

From this repository, use the actual existing entry points:

```sh
python contracts/template-v1/test_contract.py
npm ci --prefix contracts/template-v1 --ignore-scripts --no-audit --no-fund
npm test --prefix contracts/template-v1
python -m pytest -q scripts
python scripts/test_spec_tools.py
python scripts/check_template.py --all
python scripts/check_managed_catalog.py
python scripts/check_docs.py
python scripts/sync_template_reference.py --check
```

Install the pinned specification dependencies from scripts/requirements-spec.txt first. Full cross-language checks also require the Python interpreter selected by PYTHON to have those dependencies. Relevant native local runtimes and their locks are defined by .github/workflows/e2e.yml; a missing prerequisite is not a template pass.

### Remaining execution sequence — planned, not executed here

1. Verify the latest exact-head owner checks/reviews and source locks before cloud effects. Use current source CLI/SDK; published CLI0.5.10 and package metadata a7 do not prove v1 support.
2. Obtain the existing PostgreSQL URL/network/CA configuration and a Codex model service that supports real Responses tool rounds through private operator configuration. Validate existing FC role, ACR, Sandbox region/access and connectivity. Keep values outside Git and reports; do not create replacement RDS instances merely to obtain evidence.
3. Acquire the exact reviewed agents-api source with `abx template init`, then prepare the documented Python/httpx host hook. Set matching native env references privately. Preview with `abx deploy . --name <owned-app> --plan`; build/deploy with the documented root commands only after prerequisites are ready. Record ownership before mutation.
4. Reuse one controlled application and state store. Execute actual Qwen/Codex tool/file tasks through its business Gateway using agents-api/scripts/smoke.py. The hook already checks two dependent turns, downloaded results, close/retained artifacts and deletion. Do not substitute a version check, fixture adapter or local Docker case for this cloud result.
5. Verify update behavior: keep an old Session across a new revision, continue through its recorded Worker revision, then close it and drain/delete the unused revision. Preserve private recovery state on uncertain outcomes; never blindly repeat non-idempotent creates.
6. Verify applicable event streaming/cancellation and durable queries with their actual supported scope. Delete only recorded owned resources, independently query absence, and record borrowed databases/networks/domains/volumes plus any retained build artifacts. A cleanup failure remains a failure/blocker.
7. Only after the core new cloud cases pass, hand over to the blogs and Registry topic records below. Finish bilingual rendered links/interactions and normal coordinated merge/readback. Do not close Issue309 or claim package/catalog publication from a source merge.

### Existing evidence and retained replay sources

- [Resource migration](../../../evidence/verify/2026-11-12-template-v1-migration.md), [Core consumer checks](../../../evidence/verify/2026-11-12-template-v1-reader-consumers.md), [test-reader correction](../../../evidence/verify/2026-11-12-v1-template-test-readers.md), [buffered-log observation](../../../evidence/verify/2026-11-12-next-hmr-buffered-observation.md).
- [Final local Server/Guest/model/source acquisition](../../../evidence/verify/2026-11-12-agents-api-final-local-validation.md) preserves current local versus historical-image scopes.
- [Retained local replay sources](../../../evidence/verify/2026-11-12-agents-api-local-replay.md) now keep the exact guest driver and offline verifiers in this owner. Their hashes identify the original scripts; copying them does not establish a new model run.

The real Qwen case proves the same bridge Session/workspace and independent file results. It does not independently capture a native CLI resume ID; second-turn wire event counts include replay. Keep that boundary when writing any later article.

## Alternatives considered

Leaving required instructions only in workspace artifacts breaks standalone contribution and handoff. Copying one full mutable plan into every repository creates competing authorities. Moving credentials, large caches, binaries or raw sensitive logs into Git is rejected. Each owner therefore keeps its own operations and links the other owners.

## Dependencies

Tracking: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/309. Cross-repository links refer to owner branches
and do not assert that pending work is merged or published.

- [agent-sandbox owner operations](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/blob/feat/template-v1-parser-20261112/.agents/notes/proposed/process/2026-11-12-agents-api-delivery-operations.md).
- [python-sdk owner operations](https://github.com/Alibaba-Agent-Sandbox/python-sdk/blob/feat/template-v1-runtime-20261112/.agents/notes/proposed/process/2026-11-12-agents-api-delivery-operations.md).
- [registry owner operations](https://github.com/Alibaba-Agent-Sandbox/registry/blob/feat/template-v1-registry-20261112/.agents/notes/proposed/process/2026-11-12-agents-api-delivery-operations.md).
- [blogs owner operations](https://github.com/Alibaba-Agent-Sandbox/blogs/blob/docs/agents-api-owner-records-20261112/.agents/notes/proposed/process/2026-11-12-agents-api-delivery-operations.md).

## Test Strategy

This follow-up verifies record links, seven-section notes, replay-source hashes and Python syntax, JSON snapshots, documentation checks and whitespace. It does not rerun paid models or create cloud resources. Earlier product checks retain their exact source identities; new CI is independently required.

## Acceptance criteria

All necessary continuation steps are reachable from .agents/README.md. Owner records can be used without workspace artifacts. Core cloud acceptance and both topics remain explicitly incomplete until their real evidence and normal delivery gates close.

## Evidence

- [Record-placement verification](../../../evidence/verify/2026-11-12-agents-api-delivery-operations.md).
