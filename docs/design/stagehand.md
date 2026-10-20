# stagehand

## Purpose

Serve real Node Stagehand4 browser actions in a newly owned Express sandbox for trusted users. [Issue68](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/68). Native local-browser act plus optional typed text extract is the supported slice, not Browserbase SaaS or a separate autonomous agent.

## Capabilities

Actual upstream localBrowser.connect with the disclosed extensionId forwarding fix, extension-backed Stagehand.create/act/extract, PNG screenshots, ephemeral private profile. Explicit upstream ClientLLM callback maps structured text/images to the approved compatible model base. No Browserbase account, gateway, cache, cloud browser, arbitrary extraction schema or persistent login is selected. The wrapper never fabricates browser actions or model output.

## Exposed API

[English](../../stagehand/README.md#command-reference) and [Chinese](../../stagehand/README.zh-CN.md#命令参考) enumerate scalar named parameters/results. stagehand_version returns actual4.3.0; setup only booleans; offline self_test returns STAGEHAND_NATIVE_OK after real navigation/title/PNG; stagehand(task,url,extract_instruction='',command_timeout=180) performs actual act and optional extract, saves an exclusive PNG. Runs fixed Node argv worker.mjs with an anonymous memory request, not a shell or user code. One active native process per server; own process-group/pidfd/marker cleanup includes detached workers.

## How to build

[Dockerfile](../../stagehand/Dockerfile): Alibaba basev0.0.49, generation2, Python3.13, official SHA256-pinned Node24.16.0, npm ci with a full integrity lock for Stagehand4.3.0 and Zod4.4.3, Playwright1.58.0/Chromium1208/145.0.7632.6. Pinned server sourcee2cb27e with existing optional injected wheel shape. Non-root user, WORKDIR/home/user/app, explicit serve/healthcheck9000, no CMD/ENTRYPOINT;8GiB rootfs budget. Steps adapter preserves exact COPY hashes and official bounded browser asset cache; no cloud credentials enter CI.

## Express feasibility

Feasible: slice

Limiting factor: native local Chromium/extension compatibility and authorized structured model output; no nested VM, KVM, Docker or privileged capability. CPU2/RAM4096. Native4 ModelConfig lacks baseURL, so use the official ClientLLM generation extension point; a direct OpenAI-compatible Chat Completions transport is not a substitute browser agent. No claims for Browserbase cloud or other providers.

## Risks

Pages can use sandbox network access; only trusted authenticated callers and disposable sandboxes without valuable credentials. Explicit chromiumSandbox=false relies on outer sandbox isolation. No hostile-code/tenant separation is claimed. Model base is explicit HTTPS (literal local HTTP for authored development), no redirects; secrets pass by anonymous stdin, not browser env/argv/files; callback requests/replies/deadlines/calls and process output are bounded. Per-call private HOME/cache/profile and exact owned descendant cleanup; artifacts are exclusive random names, symlink directory rejected, own partial artifact removed on failure. Caller originals and other resources stay untouched. Upstream MIT license retained; wrapper Apache2.0.

## Test plan

L0 strict checker, docs/records, actual authored Python guard/process/deadline/overflow/memfd controls and Node callback text/image/schema/HTTP/failure/budget tests. These are no-model fixtures, not native/cloud proof. HTTP controller checks health/schema/invalid parameters/missing model and optional native version/browser; absence is SKIP unless required. L1 actual image native4.3.0 import and pinned browser self-test. L2 canonical native steps deploy → official READY → actual Python SDK Sandbox.create → CLI/SDK native smoke → independent owned sandbox/template absence. L3 separate fresh owned SDK model server and nonce fixture: one genuine semantic click, independent HTTP click/receipt state, native text extraction of the fresh receipt, exact final URL, independent PNG download/decode/hash and owned process/file/native state cleanup. Missing model fails required tier; fake response markers never qualify it. Native current acceptance remains pending until immutable receipts exist.

Primary sources inspected2026-10-20: [fixed4.3.0 npm metadata](https://registry.npmjs.org/@browserbasehq/stagehand/4.3.0), [upstream v4 local browser](https://github.com/browserbase/stagehand/blob/main/packages/docs/v4/configuration/browser.mdx), [official ClientLLM callback](https://github.com/browserbase/stagehand/blob/main/packages/docs/v4/configuration/models.mdx). Pinned package types/source and SHA512-integrity-verified tarball are authoritative over moving main docs or v3 examples. SDK4.3.0 requires Node>=22.18.0; the base Node20 is replaced. Native ModelConfig does not accept baseURL; unsupported v3 options are never silently supplied.

Template1.1.0 compatibility decision: actual fixed Chromium145 returned CDP code-32000, method Extensions.loadUnpacked, message Method not available. The SDK4.3.0 connect schema accepts extensionId but drops it in the factory. Preload only the unchanged bundled extension in an owned Chrome process/profile, observe its actual service-worker ID, and forward that public option with a one-site exact-SHA256-gated source patch. Default native connect behavior stays unchanged when no ID is supplied. Runtime requires patched source SHA256bdf3cd62126c1529e8a889cae17fd098303e24e962e491a4b20786de72c369e0. Native Stagehand still performs initialization, DOM/actions/extraction; no assistant/browser action simulator. Offline self-test serves fixed HTML only on owned loopback HTTP, sets actual viewport1024x768, verifies title/PNG and destroys Chrome/profile/server. All1.0.0failures remain immutable;1.1.0requires new L1/steps/model/cleanup proof.

Current1.1.1 actual SDK-created native Express steps and real qwen3.8-flash act/extract passed on2026-10-20, source9b2328234ae9eb914b258433f595e22cd226adff. Three model calls, independent click count1/fresh receipt match, SDK PNG15192bytes decoded1024x768 and SHA256; own process/listener/file/private native state, outer sandbox/template and private OSS cache absence passed. Non-model HTTP13/0/1model-only skip is separate from actual native model PASS. Image L1 is separate, not an actual-image model deployment. Preserve all1.0.0/1.1.0failures; the earlier1.1model failure root cause remains unproven. [Final evidence](../../.agents/evidence/verify/2026-10-20-stagehand-native-final.md).
