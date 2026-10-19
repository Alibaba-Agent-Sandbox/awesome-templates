# Decision: Authenticated standalone browser IDE
Status: proposed

## Problem

Issue53 requests an actual browser IDE under Express non-root/rootfs constraints with password authentication.

## Decision

Pin official standalone4.141.0 architecture assets and digests; isolate config/state/extensions per owned instance. Require password, preserve caller files/config, and separately verify real authentication/workbench and process/kernel cleanup.

## API Design

Version/start/status/stop/self-test commands. Private owner nonce plus Linux pidfds pin upstream worker identity; WNOWAIT holds the original leader until group signaling completes. Private config0700/0600, no credential-bearing response/log API. Cleanup uncertainty fails and retains authority.

## Alternatives considered

Floating vscode images violate base/pin contracts. Auth-none exposes the IDE without its intended password. Parent exit or a raw TCP connection cannot prove cleanup: this operator environment accepts empty-port connects through its proxy. Kernel listening tables and owned process identities are required.

## Dependencies

Official fixed MIT asset, bundled notices, SDK e2cb27e, Linux pidfd/procfs and source-step preparation from PR121. No model account. Issue53 stays open until actual cloud/current-head CI/merge gates.

## Test Strategy

Real local auth/workbench/port forwarding plus lifecycle/config/env tests; startup deadline and unrelated-listener/ownership negatives; true image/version/rootfs and Express CLI+SDK/external HTTP/owned cleanup. WebSocket/terminal interaction is not inferred from HTML.

## Acceptance criteria

Complete bilingual docs/design/license, actual behavior and lifecycle evidence, image/Express and latest-head CI, ordinary verified merge; unrun WebSocket/terminal remains explicit.
