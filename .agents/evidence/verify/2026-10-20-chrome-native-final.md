# Original headed Chrome — final1.0.5

Status: PASS for the stated original native image/Express desktop/API/cleanup scope.
[Issue61](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/61),
[PR168](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/168).

## Provenance

Actual runtime/controller sourcecd144246bcd3e2ba37865d90e24cba612db8b11b,
original Chrome-for-Testing145.0.7632.6/Linuxx64, official175440843-byte ZIP,
SHA256b5e3195041af345a668d110f5daf5581961fa3608626ea588c97dd0fe81c4e38.
Archive digest is controller-measured, not an upstream-published checksum.
Original archive/notices remain installed; root-readonly generated provenance
binds actual native binary SHA checked at invocation. Exact original Debian
Xvfb/Openbox/x11vnc/noVNC/TigerVNC dependencies and isolated full Python hash lock
are in the Dockerfile; no Python Playwright runtime or substitute browser.

Actual noneditable operator client source d4d93e8cbb986f33a8868f7a4139ed0edb49eaba,
client version0.3.0, in-image servere2cb27e24fde0a67112f82b8d44af463445a5d1a.
Official native CLI0.4.1 archive SHA256
766b0b10c3e4c633632dad503ae7750183a8be41974a9d048f060836f8cb0c44.
External controller SHA2565753cbf423f077d45c549c3fb5686b8d3071bfcd7ee3078903277096a3fab2ae.

## Actual image and resource observations

Same-source [L1 run39512397976](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/39512397976)
PASS: actual image build, source server wheel, non-root workspace and original
headed CDP/authenticated VNC/PNG native smoke with owned cleanup. Image rootfs
1689714688bytes. Native image smoke actually measured /dev/shm67108864bytes,
memory_limit=max and cpu_quota="max 100000". CPU/memory were unrestricted in this
image-user run; no combined2GB/64MiB stress-test claim.

The actual Express manifest declares2vCPU/2048MB. Its native desktop measured
1024x768 and /dev/shm1031241728bytes; cgroup2 memory/cpu paths unavailable.
Declared profile is not a peak-memory measurement. This current Express
observation differs from the older survey's64MiB observation; they are not
silently conflated. No Docker/KVM/GPU was required inside Express.

## Actual SDK-created native Express

[Receipt](../../../chrome/evidence/express-2026-10-20T230349Z.json) and
[provenance/full HTTP](../../../chrome/evidence/verification-steps-2026-10-20T230349Z.json):
published immutable COPY, canonical native steps, official READY, actual Python
SDK Sandbox.create, native CLI/SDK smoke and full external HTTP30PASS/0FAIL/0SKIP,
156.468seconds. Image acceptance is separate from step acceptance.

Actual external original CDP discovery/Browser.getVersion/WebSocket and fresh
native fixture; original noVNC UI and password-authenticated RFB frames; native
CDP click then real VNC pointer click, independent DOM counter change and matching
visible redraw. Real VNC PNG saved to an exclusive owned workspace path and
independently downloaded/decoded/bytes/SHA256/content-region checked. A fresh
post-return unpredictable ACK rechecks exact target bytes. Valid public SDK
chrome_open navigates to about:blank; independent external CDP confirms the
result. Start idempotence and readonly status passed.

## Ownership, failures and limitations

Owned screenshot removal, native/private HOME/profile/display/socket/lock/listener
absence and independent outer sandbox/template plus exact private OSS object/
bucket absence all PASS. No owned live cloud resource remains. Generated VNC
password stays private to authorized start output, not argv/URL/log/receipt.
Browser environment excludes operator cloud/model/GitHub secrets. --no-sandbox
relies on the disposable outer sandbox; private profile is removed on stop while
caller screenshots persist unless removed. Original third-party licenses and
notices are retained. No model/benchmark/other-provider qualification.

All original failures remain unchanged in [preparation](2026-10-20-chrome-visible-cdp.md)
and dated receipts. The actual white VNC center pixel was the software pointer:
both original VNC fixture PNGs center255,255,255, three off-cursor regions10,230,20,
matching original CDP capture. Independent predefined content regions fix the
verifier; DOM/input/artifact/cleanup gates remain mandatory. Earlier viewport/
activation hypotheses were insufficient and are not rewritten as passes. A
separate diagnostic smoke override intentionally never qualified the template;
its per-session cleanup error was not claimed as pass, outer/OSS absence passed.

## Repository validation

Current wrapper/protocol regressions22PASS0.35seconds, including actual authored
RFB/DES/rawframe/pointer, HTTP auth, native CDP activation, pointer-aware content
validation and retained exact display journal on cleanup retry. Earlier integrated
shared regressions51PASS; final source-only HTTP/spec/docs/receipt/latest-head CI
checks are publication gates recorded after execution. Source-only native omissions
never establish a native desktop/provider pass. No AI-generated image or substitute
framebuffer is used.

Publication checks: strict all-template0violations;179public Markdown documents and3explicit records0link failures; both actual bilingual SDK snippets syntax PASS; final source-only HTTP7PASS/0FAIL with native GUI explicitly SKIP. Full57spec checks PASS13.205seconds (exact log duration verified at publication). Current receipt audit and latest-head CI remain final delivery gates.
