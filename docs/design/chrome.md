# chrome

## Purpose

Deliver genuine headed Chrome automation and a visible interactive desktop for [Issue61](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/61), without a floating upstream container or a substitute browser implementation.

## Capabilities

Shell/files/code/ports; original headed Chrome-for-Testing145.0.7632.6, private Xvfb/Openbox, native CDP and password-authenticated noVNC. No benchmark/model/OSWorld score or other provider qualification.

## Exposed API

[Command reference](../../chrome/README.md#command-reference) documents all eight scalar commands, bounds, returned schema and ownership. Start creates/reuses only the server-owned desktop; status/setup do not launch. Open navigates native CDP; screenshot captures actual authenticated VNC into an exclusive0600 workspace PNG. Stop removes owned processes/private state/display/ports and preserves caller screenshots. Smoke refuses an active caller session.

## How to build

[Dockerfile](../../chrome/Dockerfile): Alibaba generation2 basev0.0.49, Python3.13/Linuxx64, exact Debian desktop/VNC package pins, full isolated Python hash lock and pip check, official175440843-byte Chrome ZIP with controller-measured SHA256b5e3195041af345a668d110f5daf5581961fa3608626ea588c97dd0fe81c4e38. This is not an upstream-published checksum. [Immutable dependency list source](https://github.com/microsoft/playwright/blob/961381ec73a9fa2661d92504eab1a6bd6eaffc75/packages/playwright-core/src/server/registry/nativeDeps.ts); no Playwright Python runtime is substituted. Original ZIP/notices remain installed; generated root-readonly provenance binds actual native binary SHA checked before calls. server package 0.4.0a3. Non-root user,8GiB rootfs guard, no CMD/ENTRYPOINT. Canonical steps exact archive cache retains integrity and15KB wire guard.

## Express feasibility

Feasible: slice. Limiting factor: workload/resource coverage is bounded by the recorded controlled native desktop task. Actual Linuxx64/declared2CPU/2048MB/noDocker/noKVM/noGPU Express profile passed; /dev/shm1031241728bytes and cgroup2paths unavailable. Separate actual L1 native image smoke measured64MiB shared memory with unrestricted CPU/memory. No combined2GB/64MiB stress-test claim. Ports9000/9222/6080 exposed; native9223/5901 loopback only. Browser --no-sandbox relies on the disposable outer sandbox boundary; --disable-dev-shm-usage accommodates small shared memory.

## Risks

Private0700 HOME/profile/Xauthority, generated8-character password via stdin to tigervncpasswd,0600 password file; never password argv/URL/log/receipt. Start returns password only to authorized caller. Provider gateway access plus optional ABX_SERVER_TOKEN Bearer protects CDP; noVNC has actual VNC authentication. Minimal browser environment excludes operator secrets. Own process group/nonce/pidfd cleanup covers detached descendants; display removal checks recorded UID/PID/socket/lock inodes. Reserved ports occupied by others fail closed. One serialized session/server; client disconnect does not cancel it. Native CDP grants browser authority and URLs/files may retain private content. Original third-party licenses remain in the image; see [notice](../../chrome/UPSTREAM-NOTICE.md).

## Test plan

L0 authored URL/secret exclusion/exclusive PNG/private IPC/process cleanup/RFB3.8-DES/rawframe/pointer/HTTP Bearer regressions and source-only HTTP with native omissions explicit. L1 actual headed native CDP/VNC/PNG smoke and image build. L2 published-source canonical steps, official READY, actual SDK Sandbox.create, CLI/SDK smoke, full external CDP version/WebSocket, noVNC static client, actual authenticated RFB green-frame capture, real VNC button input with independent CDP counter change and blue-frame capture, SDK screenshot independent file/bytes/hash/PNG/pixel checks and fresh post-return ACK. Finally independently verify owned PNG/process/private display/ports plus sandbox/template/OSS absence. No model test applies. All unrun/failed/skipped checks remain distinct from pass.

Current1.0.5 sourcecd144246bcd3e2ba37865d90e24cba612db8b11b passed actual image L1 and SDK-created canonical native Express steps/fullHTTP30/0/0 with independent owned native/private/display/ports/PNG/outer/OSS absence. Native DOM and framebuffer validation uses independent predefined content regions away from the real software pointer. Historical failures remain preserved. [Final evidence](../../.agents/evidence/verify/2026-10-20-chrome-native-final.md).

Version 1.0.6 preserves the provider-resolved base path and fixed query for native CDP discovery/WebSocket and noVNC static/WebSocket routes. The provider endpoint controls host/scheme; a native discovery host is never adopted. Application and gateway headers remain separate inputs to the existing clients. See [Issue 217](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/217); previous 1.0.5 receipts remain historical.
