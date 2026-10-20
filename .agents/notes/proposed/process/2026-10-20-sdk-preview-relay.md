# Decision: explicit operator-local SDK preview

Status: proposed

## Problem

[Issue53](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/53) requires real browser IDE behavior. Actual Express and a separate minimal HTML control confirmed the configured default FC domain forces HTML attachment downloads. Direct mode remains blocked without a suitable mapped preview domain.

## Decision

Add an explicit operator-local HTTP/WS relay using the native SDK endpoint, fixed upstream HTTPS verification, loopback Host/Origin/entry checks and isolated RAM cookies. Normalize only HTML attachment disposition. Keep the direct controller and all prior failed receipts. Extend the browser controller with explicit sdk-local mode; require actual workbench/PTY/editor and independent files SDK bytes plus owned cleanup before qualification.

## API Design

scripts/preview_proxy.py borrows a connected sandbox and exposes a local-only URL. It closes only local resources. The selected upstream is immutable, query auth cannot be overridden, external redirects are rejected, HTTP bodies stream, and WS text/binary/subprotocols pass through. The controller owns its separately started password IDE and nonce file, with cleanup even after browser teardown failures. No image/runtime command changes.

## Alternatives considered

An existing mapped custom domain supports direct mode. Local browser interception would not provide a reusable operator operation. The explicit relay can be used from a normal browser and validates the real remote application without account DNS changes.

## Dependencies

Paired native SDK; operator CPython3.13/Linux amd64; exact hashlocked aiohttp3.14.5 and transitive releases; existing Playwright1.58.0/Chromium1208/certutil browser controller. Dependency review selected the patched release before publication. Template code-server1.0.0 runtime/archive inputs stay unchanged.

## Test Strategy

Actual local HTTP/WS fixtures test auth/query/cookie isolation, HTML-only normalization, preserved downloads/gzip bytes, subprotocol and binary/text frames, and independent kernel listener release even after close failure. Actual in-memory TLS handshakes reject unknown CA and accept explicit trust; disabled TLS contexts are rejected. The environment's Host/TLS interception prevented using those negative network fixtures directly, so Host validation is tested before forwarding and crypto policy uses MemoryBIO. Genuine Express HTTPS/browser verification remains mandatory.

## Acceptance criteria

- Normal local operation and explicit mode documented in both languages; direct-domain failures preserved.
- Real Express browser login/workbench, PTY nonce, Monaco edit/save and independent SDK bytes pass with upstream TLS enabled.
- Local listener, owned IDE/file and outer sandbox/template/registry cleanup are independently confirmed as applicable.
- Exact source/controller/relay hashes, current-head checks and normal merge precede qualification and Issue closure.
