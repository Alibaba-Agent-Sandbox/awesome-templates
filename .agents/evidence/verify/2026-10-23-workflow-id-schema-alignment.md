# Workflow ID schema alignment

Result: PASS (local schema scope)

Scope: `spec/template-v4.schema.json`, `spec/workflow-portion.schema.json` and `scripts/test_workflow_contract.py` on top of 0e26f972acf96eddd4d5c26e58fcd556f6e0a51d. Issue: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/194; PR: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/195.

The full manifest schema and its workflow-only projection restricted workflow names/default_workflow to hyphens. The shared Python/CLI contract accepts underscores. Both local schema fields now use `^[a-z][a-z0-9_-]*$`. The full-schema regression moves the real skeleton workflow to `application_image`, selects it as default, and validates the complete manifest. Service names and build-profile naming have not changed. No canonical contract data or source lock changed.

Executed with Python 3.11 and locked specification dependencies:

- `python -m pytest -q scripts/test_workflow_contract.py scripts/test_managed_catalog.py`: PASS, 37 tests.
- `python scripts/sync_workflow_contracts.py --check`: PASS.
- `python scripts/check_docs.py`: PASS, 221 documents, zero link failures.
- `git diff --check`: PASS.

An initial command named a nonexistent `scripts/test_managed_templates.py` and collected no tests; the corrected managed-catalog command above passed. No image/native/cloud execution was required or claimed for this schema correction. Remote checks must run on this new commit.
