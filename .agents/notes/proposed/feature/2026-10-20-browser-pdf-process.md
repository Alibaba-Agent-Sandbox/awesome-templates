# Decision: actual PDF artifacts and owned browser-script processes

Status: proposed

## Problem

[Issue22](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/22) explicitly requires screenshot/PDF behavior. PDF was absent. Review also reproduced a workspace script returning nonzero while its ordinary background child survived.

## Decision

Version2.2.0 adds real Chromium A4 PDF and fixes generic run ownership/output/deadline behavior. Preserve2.1.0 MCP as a separately qualified component/history. A new profile requires fresh image/Express acceptance. Source dependency: [MCP PR142](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/142).

## API Design

pdf(url,landscape=false,print_background=true,timeout_s=30) returns path/bytes/format.256KiB URL/no NUL; typed flags;1–120seconds;16MiB post-render file limit. Worker config uses private stdin, private HOME, filtered environment. Generic run preserves caller HOME, filters credentials/loaders, caps both streams256KiB and reserves group identity plus marked pidfds for ordinary/detached children on every outcome. Rootfs du build limit8GiB.

## Alternatives considered

A static PDF marker cannot prove rendering. Direct in-server page.pdf lacks an independent hard process deadline. Killing only a reaped script leader leaves descendants. Existing immutable2.1.0 receipts cannot certify new2.2.0 source. The managed process helper reuses existing identity-safe lifecycle definitions with per-call isolated state; no shared MCP state is modified.

## Dependencies

Existing pinned Playwright1.58/Chromium1208/native MCP0.0.83, Linux procfs/pidfds and paired SDK. No new model key or PDF library. Preserve upstream notices and provider-owned start/health configuration.

## Test Strategy

Before-fix actual nonzero-script child regression fails and safely cleans its identified fixture child. After correction6 actual native cases PASS: child absence, portrait/landscape PDF bytes/geometry, symlink refusal, deadline/output bound and environment filtering. Full real local HTTP37 PASS/0FAIL/0SKIP including remote PDF downloads/orientation/deletion and preserved native MCP behavior. Fresh actual cloud/source hashes/cleanup and current-head CI required.

## Acceptance criteria

All screenshot/PDF/original browser/MCP behavior passes without skips in actual Express, independent remote artifacts and owned cleanup; exact new profile evidence; bilingual API/limits/compatibility/step operations and image-size check; normal verified merge before Issue22 closure.
