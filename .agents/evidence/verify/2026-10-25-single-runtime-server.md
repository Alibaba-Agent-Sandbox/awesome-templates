# Single application runtime guide verification — 2026-10-25

Status: PARTIAL (local documentation checks PASS; remote CI, review and authorized merge pending).

## Inputs and scope

Base: 4229b6c4d96675a05bd0bef031fb36d43f138d14. Only the English/Chinese runtime guide, corresponding specification sentence and owner records change. No Python/runtime, manifests, recipes, versions or historical receipts change. The retained Aider PR88 link is explicitly historical.

Public installed Python 3.13.13 environment: agent-sandbox-client and agent-sandbox-server 0.4.0a6; ProviderSandbox resolved from site-packages with ambient PYTHONPATH removed. No installation performed for this work.

## Executed local verification

- `python scripts/check_docs.py`: PASS, 222 current documents, 0 failures (no network/cloud calls).
- Parse and compile both runtime guides' Python blocks using ast/compile: PASS, 2 blocks. Execute their import statements against installed public 0.4.0a6: PASS.
- Bind the documented ProviderSandbox.connect and application_client arguments against actual installed signatures; check ProviderSandbox.close and returned ServerClient.aclose: PASS. This is an API inspection, not a cloud invocation.
- Compare both language examples and python-hello's actual hello signature/port: PASS. Same Python program in both languages; SHA256 `ce85a3ed33f1cc85f818b85dfdd33663ab21deb6bd3eb11767d9a2196c57f0ba`.
- Introduced cross-repository authoring/provider guide targets: PASS, all 3 files exist on their remote main branch.
- Configured-secret scan: PASS, 7 scoped files, 0 known-value matches.
- `git diff --check`: PASS.

An initial local verification helper itself imported the nonexistent agent_sandbox.client module and failed before inspecting the blocks. The guide never contained that import. Correcting only the verifier to inspect the actual ServerClient module yielded the results above; this is not a product failure or a discarded cloud attempt.

## Limits and cleanup

The displayed full program was not executed against a new sandbox for this docs task; syntax/import/signature checks cannot be called a new CLI/SDK/HTTP end-to-end pass. No cloud, model, image or dependency mutation occurred; there are no owned resources to clean up. Existing public launch evidence remains separate. Required latest-head CI and review are pending. Merge is held until the frozen OpenSandbox matrix completes, and linked Issues remain open for their broader acceptance.
