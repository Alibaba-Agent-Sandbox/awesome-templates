# Verification: Current CLI template guidance

- Date: 2026-11-25
- Result: PARTIAL — local documentation/help checks pass; final publication prerequisite and current-head CI/merge are separate gates.
- Scope: root READMEs and shared template-use guide in both languages, associated decision/index/changelog.
- CLI source inspected: `c268608d6a3f917c6d07b7feaa24ab54f25e8fdf`, the verified merge of [CLI PR269](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/pull/269).

## Publication dependency

The final installation examples target CLI `0.6.0-alpha.0` and Python client `0.5.0a0` explicitly. At this preparation checkpoint, their actual public readback remains outstanding. [CLI PR271](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/pull/271) and [Python PR174](https://github.com/Alibaba-Agent-Sandbox/python-sdk/pull/174) own the candidates and release gates. The templates PR stays Draft until both public readbacks and all its current-head checks pass. These examples are not a publication claim; installing the public packages was not verified by this documentation run.

## Reader path and source review

PASS: the quick start deploys one named python-hello instance, reads its status/startup logs and deletes its recorded owned resources. The shared guide retains its existing Python SDK/HTTP hello examples using the returned Sandbox ID. The template's `@command` functions and `/commands/hello` route are unchanged.

PASS: inspected the merged CLI API guide, scaffold and command declarations. Target-first invocation requires a locally bound explicit OpenAPI 3.1 contract; the existing python-hello source contains no registry/OpenAPI binding. The guide now links the complete CLI binding example without claiming automatic discovery or adding duplicate configuration files. Removed wrapper calls and the old nested platform-tool spelling from these four documents.

The 94 template-owned README documents still containing older CLI wrappers are outside this correction; they were not migrated or certified for 0.6. The bilingual shared installation guide explicitly tells readers to follow each template's stated CLI version and directs 0.6 business calls to the SDK/HTTP examples or explicit binding guide.

## Actual checks

| Check | Result |
| --- | --- |
| Built merged-source CLI `deploy --help` | PASS; name, Sandbox lifetime and build-deadline options present |
| Built CLI `status --help`, `logs --help`, `delete --help` | PASS; existing-target syntax and relevant options present |
| Built CLI `download --help`, `exec --help` | PASS; root platform commands and positional paths present |
| Built CLI `sandbox --help` | PASS; TARGET/OPERATION interface present |
| `python scripts/check_docs.py` | PASS; 236 documents, 0 local link failures |
| Existing Markdown checker over all 10 changed/new Markdown files | PASS; no local link/fragment failures |
| Python AST parse of the four SDK/HTTP code blocks in both languages | PASS; syntax valid |
| `git diff --check` | PASS |

All seven executable help invocations exited 0. This verifies parser/help contracts, not a fresh template deployment or business call. No new cloud resources or services were created. Template image/runtime pins and historical provider evidence remain unchanged; only the guide's host installation selects the target client preview.
