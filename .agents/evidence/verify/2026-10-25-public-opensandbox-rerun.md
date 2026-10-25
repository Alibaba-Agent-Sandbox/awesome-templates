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


Follow-up to reviewed head 3defd4b37cc267e046cdcbf255a250e0891b8176: its new canary 40191975460 passed browser-automation (37 assertions, zero skips), python-hello (21, zero skips), and openclaw (11, one explicit model skip), with independent cleanup. Chrome exited before assertions: the gateway-header edit accidentally altered a function signature. This is a verifier syntax defect, not a runtime failure; restore that signature and compile all catalog controllers before cloud execution.

Native attempt 40191973586 established that the CLI had returned valid JSON whose stdout equals 42. GitHub Actions is intentionally detected as CI and selects JSON automatically; no process output was lost. The original bare-text-only assertion was a harness error. The follow-up explicitly checks JSON and separately checks ordinary text mode with CI markers removed, then continues the real SDK/interpreter tests. Original two failed native attempts remain unchanged.


The cursor-agent and devin invalid-credential/no-account fixtures now honor their existing explicit `E2E_REMOTE_SANDBOX=1` opt-in for a provider-resolved loopback gateway. A localhost forwarded port can route to the real isolated Docker guest, so its address is not evidence of a mock. The separate real-model business guard is preserved. Two focused regressions verify the native authentication fixture is reached only with the explicit opt-in, including loopback endpoints; these are unit checks, not cloud proof. Combined focused suite: 46 passed; all catalog controllers compile.


Native follow-up run 40192740450 at 6aa6f2fac8635aa0a82bea266dde603225de920a passed the complete published native journey: JSON and plain developer CLI exec, SDK shell/files, real native interpreter context persistence, isolation, program errors and deletion, with independently confirmed SDK/Docker absence. Three foreign provider IDs remain NOT_APPLICABLE with explicit compatibility rejection, not cross-provider passes.

Chrome follow-up 40192742444 passed 16 assertions through actual headed runtime/noVNC and DevTools HTTP discovery, then failed a native WebSocket handshake. This remains under investigation. Add only controlled numeric HTTP status and provider endpoint structural booleans to aid diagnosis; do not expose addresses, IDs, tokens, remote content or raw exception messages.
