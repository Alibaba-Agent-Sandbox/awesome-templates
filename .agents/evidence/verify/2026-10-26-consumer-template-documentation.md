# Consumer template documentation verification

Date: 2026-10-26
Result: PASS for scoped local checks; remote CI/merge/public sync pending
Issue: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/235
Base: 1a8c81f59d22fe10b987ffe5f9b59d15b5ed0ded

Scope: 46 source + four managed catalog entries, both README languages; shared usage/runtime guidance, skeleton, contributor/spec documentation, README checker and its regressions. Runtime code, manifests, dependency locks, Dockerfiles, catalog and old evidence are unchanged. This documentation correction does not require a new template/runtime package version.

Final local commands, results, source hashes and independent review are recorded below before commit. A documentation or local model test does not certify image builds or any cloud-template matrix.

## Host and resource limitations

The official Docker client/daemon/rootless binaries were installed in the previous local attempt; no working engine was established. On this run, `sudo -n su -c 'id'` failed because sudo.conf ownership is invalid for sudo and the container has no-new-privileges enabled. The process is non-root with no effective/bounding capabilities. User authorization cannot remove these host-enforced restrictions. No cloud credentials were added to CI, no cloud resources were created by this documentation task, and no default Express Docker-to-ACR pass is claimed.

## Initial failures preserved

The first full README checker found missing explicit SDK distribution names and HTTP metadata in rewritten examples. Those documentation omissions were corrected without weakening the checker. A raw shell-fence scan found four managed examples containing unquoted `<sandbox-id>` tokens; all managed instances now use a quoted exported sandbox ID. The skeleton's same placeholder was corrected too. Cross-review found Aider's required Git initialization was missing from the SDK/HTTP paths and a false native-tool-calling requirement; both languages now match the whole-file adapter. Cross-review also removed a next-app historical failure paragraph referring to a deleted section.

The first actual local OpenCode model attempt passed wrong-token rejection (401), the pinned 1.19.0 version and setup/config checks, then failed with CommandExecutionError. Its original sanitized result is preserved separately; it is not relabeled as a model pass. The owned local server process exited. Subsequent diagnostic results, if any, are recorded separately below.

## Final local checks

Environment: Python 3.13.13, Node 22.22.2; public CLI 0.5.6, client/server 0.4.0a6, HTTPX 0.28.1, OpenCode 1.19.0. See [integrated checks](2026-10-26-consumer-template-checks.json) for exact commands/counts and [independent content review](2026-10-26-consumer-template-peer.json) for all 100 catalog README hashes. All commands below exited 0:

- `python scripts/check_docs.py`: 222 current documents, zero local link failures before the new engineering record; record links checked separately below.
- `python scripts/check_template.py --all`: zero specification failures across the 46 source entries.
- `python scripts/check_managed_catalog.py`: zero managed-catalog violations.
- `python scripts/test_spec_tools.py`: 39 tests passed. Expected negative fixtures print specification failures internally; the test runner finished OK.
- `python -m pytest -q scripts/test_spec_tools.py scripts/test_managed_catalog.py scripts/test_template_launch_contract.py scripts/test_check_docs.py scripts/test_canonical_express_review.py scripts/test_select_image_templates.py`: 113 tests and 170 subtests passed.
- `ABX=abx python scripts/test_express_cli_contract.py` with the installed public CLI: two tests passed.
- All 105 actual README files, including the root and feasibility docs: 107 Python fences (105 complete, two context fragments), 104 JSON fences and 315 whole Bash fences passed compile/parse/`bash -n`. Bash syntax checking does not execute commands. The initial report harness assumed a nonexistent root Chinese README; corrected enumeration and the rerun are explicitly recorded.
- `git diff --check`: passed. Runtime, manifest, catalog, lockfile and historical-evidence changes: none.

The [same-fixture old/new comparison](2026-10-26-consumer-template-heading-regression.json) proves the original checker rejected the four absent engineering headings; the corrected checker accepts consumer documentation while still rejecting an invented provider-pass table. The [eight local HTTP cases](2026-10-26-consumer-template-http-local.json) execute the actual bilingual snippets using MockTransport: path/query and occupied gateway headers are retained; both occupied authentication headers stop before a request; clients close. This is local mocked routing, not a provider pass.

## Actual local OpenCode model/API diagnostic

The [first failure](2026-10-26-consumer-template-opencode-initial-failure.json) is unchanged. The operator harness mistakenly inherited its own model selector rather than choosing a model supported by the configured Chat endpoint. A direct native reproduction, after adding that selector through the wrapper's model-catalog logic, reached the model service and returned HTTP 404 / model_not_found. An earlier diagnostic without the wrapper's model registration was a diagnostic setup error, not a product defect.

With the explicit template default `dashscope/qwen3.8-flash`, the [separate successful run](2026-10-26-consumer-template-opencode-model-success.json) used unmodified commands.py/config, installed client/server 0.4.0a6 and official OpenCode 1.19.0. Wrong-token HTTP 401, version, configuration, a real SDK coding task and a separate direct HTTP coding task all passed. Each task created its requested Python file and an independent Python process executed it and checked its exact output. Both artifact hashes are recorded. These are two task-command invocations; upstream model request count was not independently measured.

The local controller started `agent-sandbox-server serve --host 127.0.0.1 --port <owned-free-port> --commands <copied-opencode-commands.py> --base-dir <owned-workspace>`, used XDG directories for owned configuration/data/cache, and supplied the model key/base URL and a random application token through environment only. It called `ServerClient.commands.run('opencode_run', prompt=..., model='dashscope/qwen3.8-flash', cwd=<owned-workspace>)`, then `POST /commands/opencode_run` with X-Access-Token and a direct parameter object. Model credentials and endpoints are omitted. The owned server exited; independent process inspection found no matching owned children. No cloud resources were created. This exercises a local application contract and real model, not ProviderSandbox routing, an image build, cloud startup, a strict full-product model suite or all 50 templates.

## Delivery gates

The documentation/spec/checker patch still follows normal current-head CI. The PR image selector currently selects no runtime contexts; existing main-push image selection remains governed by its unchanged workflow. Full CI jobs and remote review are separate from local static tests. Public registry content must be fetched from the merged source, with results recorded after deployment; no publication is claimed by this local record.

Final engineering-record link check: three changed/new record documents, zero failures; scoped configured-sensitive-value scan and final diff whitespace check passed.

## Post-submission agents-cli documentation correction

Final root review identified an avoidable SDK example failure when a gateway used Authorization. The two examples now apply the same free-header logic as the shared guide: retain gateway credentials, fill free Bearer/X-Access-Token slots, and reject only when both are occupied. No runtime behavior changed. [Actual before/after snippet regression](2026-10-26-consumer-template-agents-gateway.json): six of eight local mock cases passed before (the two gateway-Authorization cases failed), eight of eight passed afterwards. Each successful case executes the actual example through session creation, event submission and session/items polling with real HTTPX MockTransport. URL path/query, gateway credentials and client closure are asserted; double occupancy sends no request.

The two changed Python fences, four JSON fences and six full Bash fences were rechecked with zero failures; current links remained 222/0 and diff whitespace passed. Earlier full-suite records retain their original checkpoint and hashes. The 98 unchanged catalog README hashes in the original independent review plus the two after hashes in this regression match all 100 current catalog README files exactly. Full current-head remote CI runs again for the new commit before merge. No new model/cloud/Docker claim is attached to these mocked cases.
