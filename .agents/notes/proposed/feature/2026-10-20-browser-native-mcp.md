# Decision: native Playwright MCP in the existing browser template

Status: proposed

## Problem

[Issue52](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/52) needs genuine MCP browser tools; existing browse commands do not speak MCP. Reinstalling Chromium would duplicate a large browser and increase Express resource pressure.

## Decision

Version2.1.0 installs official npm @playwright/mcp0.0.83 with an exact integrity lockfile and its pinned JS drivers, reusing Chromium1208 from Python Playwright1.58.0. Preserve existing named browser APIs. Reset provider qualification until actual new-image acceptance passes.

## API Design

mcp_start/status/call/stop/self_test. Native standard MCP HTTP is sandbox-loopback8931, not a new public gateway. The SDK's authenticated named transport can call tools/list, tools/call and ping. JSON object64KiB, responses4MiB; native action/navigation10/20 seconds, output10MiB. Negotiate a real MCP session; never fabricate tool results. Private HOME/config/output; filter native environment. Stop reserves the leader identity, captures marked detached workers with pidfds and independently confirms process/listener absence.

## Alternatives considered

No floating npx installer, duplicate browser, invented legacy ref argument or cloud/model keys. The actual0.0.83 browser_click schema requires target; an actual deterministic native feasibility run confirmed existing Chromium compatibility. A public unauthenticated raw MCP listener would enlarge the exposure unnecessarily; same-sandbox clients use loopback, external SDK clients use the existing authenticated command server.

## Dependencies

Existing Alibaba base/non-root/shared server, official npm lockfile and upstream Apache-2.0/MIT notices in installed packages, Python Playwright1.58.0/Chromium1208. New SDK/CLI source contracts are unnecessary. Source fallback server pin now matches the e2cb27e build-wheel profile.

## Test Strategy

Actual native MCP initialization,25 tools, real independent counter increment twice and newly generated PNG. Verify private state/environment, detached Chrome worker cleanup, unrelated listener preservation and invalid method/JSON bounds. Extend full HTTP controller and CI with actual pinned MCP. Fresh image plus genuine Express SDK-created sandbox, native smoke/full HTTP and independently verified cleanup; evaluate real platform steps separately.

## Acceptance criteria

- Native7 regression cases pass, complete old/new HTTP behavior passes without skips.
- Exact new image/runtime/controller provenance and current-version Express receipts only after independent sandbox/template/registry cleanup.
- Complete bilingual API/SDK/CLI/step instructions, catalog/design/engineering records.
- Current-head CI and normal verified merge before closing Issue52.
