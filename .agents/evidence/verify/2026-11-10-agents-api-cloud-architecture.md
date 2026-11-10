# agents-api architecture documentation verification — 2026-11-10

Result: PASS (documentation/source review scope; remote CI/publication separate)

## Scope and inputs

Baseline: awesome-templates e94ab308a74715982bb059b142518f7d6070c1c2.
Changed files: the English and Chinese agents-api READMEs, the agents-api design,
the static diagram under docs/assets and the accompanying engineering records.
No runtime, recipe, manifest or catalog change.

## Architecture review

Independent reviewers checked the module map against the current template,
bindings, published Python 0.4.0a7 managed runtime and CLI 0.5.10 deployment code.
Gateway persists requests; the FC timer invokes Dispatcher; Dispatcher invokes
the revision-bound Worker through FC asynchronous tasks. Worker drives the
Session Sandbox and stores events/artifacts in PostgreSQL. The Agent calls the
model within the Sandbox. Existing PostgreSQL and model services are required;
RDS and Model Studio are options, not exclusive dependencies. Database and network
creation are not claimed. Three FC roles share the Server image; the Guest image
is separate. ACR/RAM are deployment prerequisites, with optional existing private
network, database CA and custom-domain configuration.

Sources:
- [Template and bindings](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/tree/e94ab308a74715982bb059b142518f7d6070c1c2/agents-api)
- [Published runtime](https://github.com/Alibaba-Agent-Sandbox/python-sdk/tree/v0.4.0a7/client-sdk/src/agent_sandbox/managed_agents)
- [Published CLI deployment implementation](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/tree/v0.5.10/src/application)
- [Registry renderer](https://github.com/Alibaba-Agent-Sandbox/registry/blob/1601d5e5c2dc9d0afed3a67cc974a8c43ac09e0e/scripts/build_data.py)

## Executed checks

Python 3.13; PyYAML 6.0.3 and jsonschema 4.26.0 from
scripts/requirements-spec.txt; pytest 9.1.1 matching documentation CI.

- `python scripts/check_template.py agents-api`: exit 0, conformant.
- `python scripts/check_docs.py`: exit 0, 232 current documents, no failures.
- `python -m pytest -q scripts/test_check_docs.py`: exit 0, 4 passed.
- `python scripts/check_docs.py` with the two new engineering records: exit 0,
  no local-link failures.
- `python scripts/sync_process_runners.py --check`: exit 0, 15 helpers match.
- `python scripts/sync_controller_ownership.py --check`: exit 0, 8 synchronized.
- The original Registry `render_md` rendered both README languages with the new
  image's exact absolute URL, heading anchors and tables. Independent bilingual
  review found no blocking issue; the image alt was clarified to describe the
  Gateway persisting data rather than clients accessing the database.
- Headless Chrome rendered the self-contained SVG; the preview was visually
  inspected for readable labels, the FC role grouping and the task/data arrows.
  No script, external font, embedded secret or remote resource is needed by the SVG.
- `git diff --check`: exit 0.

## Publication and limits

The existing template-main notification and Registry synchronization publish this
content. A merge alone does not prove the live page or new asset has refreshed.
The raw main asset URL is introduced by this PR; check the branch asset before
merge and main/live references afterward. No new cloud, image, model or API
acceptance is claimed or required for this documentation-only change. Historical
acceptance records remain unchanged. No cloud resources were created.
