# browser-use

## Purpose

Run actual browser-use0.13.11 on private local Chromium for text-DOM browser tasks and downloadable PNGs, separate from model-free Playwright primitives.

## Capabilities

Native version/setup/offline CDP self-test/browser_use(task,url,max_steps,command_timeout). Real local browser only; no Browser Use Cloud, GPU/KVM/Docker, automatic extensions or delegation. Explicit15 native browser actions; no filesystem/shell/evaluate/extract/upload/PDF/search actions.

## Exposed API

Complete bilingual [command reference](../../browser-use/README.md#command-reference). Returned model result/final URL/new screenshot_path/bytes/steps/done/success. Final URL comes from actual native target info. A static done statement is never independent acceptance. One active browser operation per server, busy500; actual package and Chromium version checks.

## How to build

[Dockerfile](../../browser-use/Dockerfile): FC generation2/Python3.13, complete package SHA256 lock/browser-use0.13.11, actual pip hash enforcement/pip check. Browser-use itself uses CDP-use, not a Playwright Python dependency. An explicit Playwright1.58.0 installer selects Chromium1208/145.0.7632.6; --no-shell avoids a second headless-shell installation. Fixed SDK sourcee2cb or injected wheel, serve/healthcheck9000, chown workspace before non-root user,8GiB rootfs build gate. Hash-lock spec support dependency: [PR146](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/146), land before consumer.

## Express feasibility

Feasible: slice

Limiting factor: exact browser/package/model runtime acceptance and explicit compatible model endpoint/key. Text-DOM/use_vision=false works without a vision model. CPU2/memory2048, disable-dev-shm-usage, owned local CDP loopback argument. No cloud browser API or other provider claim.

## Risks

Private per-call HOME/XDG/profile/native filesystem, no credentials in argv or inherited browser environment; model settings enter private file stdin and explicit ChatOpenAI. Disable telemetry/cloud sync/automatic extensions and use_cloud. Exact15-action registry asserted before/after Agent construction; no arbitrary JS or local files/shell actions. Same-user hostile code remains outside these convenience restrictions; sandbox is final boundary. Model may browse private content: PNG/result are caller data. URL8KiB/task256KiB, max_steps1..20, deadline1..900seconds, model30seconds/0retry/4096tokens, max3 actions/step, action30/step60/LLM40seconds. Output256KiB per stream, PNG16MiB post-render limit; own private files/processes removed on all ordinary outcomes. Abrupt server loss still requires owned sandbox cleanup.

## Test plan

L0 actual0.13.11/Chromium145, native CDP/title/PNG, authored model JSON navigation/click and independent server counter/PNG, caller home preservation, pin/path/type/key/symlink/timeout/artifact guards, independent-model-controller negative cases. Fixtures are not real-model or provider evidence; no real model runs on operator host. L1 exact dependency hashes/version/image/non-root/rootfs. L2 true SDK-created Express CLI/SDK native smoke/full HTTP and independent cloud cleanup. L3 separate SDK model controller runs real model browser interactions, independently observes counter3/submitted nonce, reads/validates PNG, stops own fixture/server and independently checks listener/file absence. L4 only when actually executed on another provider. Steps preparation and actual execution have distinct receipts.

Current1.0.0 actual SDK-created image and strict real-model workflow pass; [final acceptance](../../.agents/evidence/verify/2026-10-20-browser-use-final.md) distinguishes native8step task success, a recovered JSON-format error, model-off HTTP scope and independently verified owned cleanup. The real native platform-step attempt exceeded1200seconds and was independently cleaned up; that attempt does not certify step support.
