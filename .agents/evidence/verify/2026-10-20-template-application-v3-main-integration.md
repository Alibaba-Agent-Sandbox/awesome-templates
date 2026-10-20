# Template application v3 current-main integration

Status: PARTIAL — local merge verification passed; remote CI/review/merge pending.

[PR #141](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/141)
reported a dirty merge while the branch head was `f84ac41` and its original base
was `ae375fb`. Fetching origin/main revealed the newer `14dfd4f`, containing the
SDK-created and Hermes acceptance work. This integration merges that main commit
into `feat/template-application-v3-20261020` without rewriting branch history.

The only content conflict was the appended engineering-record index. Both the
application records and incoming SDK creation/four-image acceptance links were
retained. The E2E workflow merged automatically; its existing SDK/runtime pins and
the application checker dependencies are preserved. No historical evidence was
rewritten. The v3 schema is unchanged, SHA256:
`afaa4a30fd24a5c5e4f4e28465d421e7076e612ab75e20c1a33c1d582c385a50`.

Environment: Python 3.13.13; PyYAML 6.0.3; jsonschema 4.26.0 in the same isolated
local validation environment as the preceding records.

Actual checks after resolution (exit 0):

- PASS `python scripts/test_spec_tools.py`: 53 tests, 14.073 seconds.
- PASS `python scripts/check_template.py --all --strict`: 26 directories conformant.
- PASS `python scripts/check_docs.py`: 126 documents, no broken local targets.
- PASS scoped new-record link/credential-pattern check and index/worktree diff checks.
- PASS conflict inspection: no unmerged paths remain.

The synthetic harness outputs in the spec suite do not establish real FC/model
execution. This merge created no cloud resources and needs no cloud cleanup. The
incoming main acceptance records retain their original provenance; this check
makes no new provider claim. Owner Issue [#139](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/139)
remains tracked through independent latest-head CI, review and verified remote merge.
