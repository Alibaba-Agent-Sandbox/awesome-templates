# Application event reserve compatibility

Status: PARTIAL — local contract checks passed; independent cloud/merge gates unverified.

Scope: scoped follow-up to `b773918`. Reliable runtime finalization reserves event
capacity for cancellation, uncertainty resolution and terminal state reporting.
The canonical application schema now requires `maxEventsPerRun >= 5`; a manifest
with limit 4 is rejected. Existing template manifests and deployment claims are
unchanged. Both specification languages and the proposed decision match.

Environment: Python 3.13.13, PyYAML 6.0.3, jsonschema 4.26.0, same isolated validation
environment as the original verification. Canonical schema SHA256:
`afaa4a30fd24a5c5e4f4e28465d421e7076e612ab75e20c1a33c1d582c385a50`.

Actual checks (exit 0):

- PASS `python scripts/test_spec_tools.py`: 53 tests, including 14 application tests, 12.802 seconds.
- PASS `python scripts/check_template.py --all --strict`: 26 directories, no violations.
- PASS `python scripts/check_docs.py`: 126 documents, no broken local targets.
- PASS scoped new-record link check and `git diff --check` before commit.

These are local schema/checker regressions and synthetic harness tests, not
runtime deployment acceptance. No cloud resources or model calls were created;
no owned cloud cleanup is necessary. Authenticated remote publication is now
available to the coordinating contributor, but this record does not assert an
Issue/PR/CI result or merge. No real FC deployment is certified here.

Publication tracking: owner Issue [#139](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/139)
is open; cross-repository dependencies are [CLI #80](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues/80)
and [Python SDK #74](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues/74).
These references do not assert PR/CI/merge completion.
