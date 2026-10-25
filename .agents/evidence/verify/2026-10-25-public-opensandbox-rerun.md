# Public OpenSandbox developer rerun

Date: 2026-10-25
Result: PARTIAL

Scope: current 46 source catalog entries and four provider-owned native identities. This is a new run; historical receipts remain unchanged.

Fresh PyPI client/server 0.4.0a1 installed with no cache from the official index; pip check passed. Initial runner unit invocation lacked httpx before package installation; this prerequisite failure remains recorded. No cloud pass is inferred from local tests.

Local checks passed: focused runner 23 tests; `check_template.py --all` (47 source directories including skeleton); `test_spec_tools.py` (58 tests). These are local contract checks, not cloud proof.

Pending: real published CLI/provider installs and 46-entry Docker-backed matrix, native OpenSandbox case, foreign identity rejection, receipts and UX assessment.

Issue: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/215

Canary attempt 1, run 40190029893 at 5ac2451615f6cab053094e0fa0bf32d86b5f91de: actual public npm 0.5.1 / PyPI 0.4.0a1 / public pinned provider and public Git python-hello launch passed both manifest commands via CLI, Python and host HTTP, wrong-token 401, runtime source identity, shell and files. Sandbox and all prepared artifacts independently absent. Overall FAIL: the new export helper incorrectly assumed a local Docker tag cannot have the owned localhost registry prefix. No image artifact was exported. This attempt remains a failure; the helper is corrected for a fresh attempt.

The full application controller stage now passes only its explicit generated service token, with unrelated operator credentials excluded. Real-model paths remain unverified.


Independent review identified that the first export metadata named the verifier checkout, not the unpinned public download revision. New attempts now resolve and pin the public Git HEAD and record `verifier_commit` separately. The original metadata is not rewritten. Independent reconstruction against exact public source 269f9cb6980ad48eea02fdc403d8daa80484e7b8, using the installed public npm 0.5.1 staging implementation, matched all 19 currently available complete staged snapshot digests. This proves equivalent public source bytes; it does not infer the exact HTTP download commit.

Run 40190606376 (46 source entries) and 40190608218 (native identities) use verifier 000abc8b3013bc95261185d8481198d1281c87a8. The native run verified three foreign-provider compatibility rejections without Docker resources and successfully launched the OpenSandbox catalog entry; it failed its generic CLI stdout=42 assertion, while cleanup was independently confirmed. Investigation continues; this is not a native full pass.

The first full controllers exposed inconsistent existing test token names and a concurrent browser HTTP request that omitted authentication. The host helper now supplies the same generated application credential through all three existing names. All 46 standalone controllers accept validated provider gateway headers separately from application Bearer authentication, including Python application clients and native browser transports. No runtime or Dockerfile changes. Focused ownership/privacy/header/controller checks: 43 passed; Markdown link check: 222 documents, zero failures. Current matrix outcomes and future corrected reruns remain separate.

Draft PR: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/216
