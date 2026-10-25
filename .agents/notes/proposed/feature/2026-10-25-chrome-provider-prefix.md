# Preserve provider-resolved Chrome endpoint routes

Status: proposed

## Problem

Chrome 1.0.5 discards a provider-resolved path prefix when constructing the CDP/noVNC WebSocket URL. Actual public OpenSandbox controllers reached native Chrome discovery but failed the WebSocket handshake with HTTP 404. Appending HTTP routes after a fixed query is also invalid.

## Decision

Use one small route-joining function for CDP and noVNC HTTP/WebSocket paths. Retain the provider base path, query, authority and authentication. Increment the template patch version to 1.0.6. Do not add a new provider contract or user parameter.

## API Design

Named commands and manifest services remain the same. Native discovery contributes only its route and optional query, never its internal authority. Both README languages explain that provider endpoints are used unchanged.

## Alternatives considered

Replacing endpoints with Docker bridge addresses bypasses the real provider path and hides the failure. A new URL registry or launch state is unnecessary.

## Dependencies

Existing urllib URL parsing and aiohttp transports. Follow-up to https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/217 and public-launch verification https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/216.

## Test Strategy

Actual local HTTP/WebSocket servers assert prefixed routes, fixed queries and separate application/gateway authentication. The old implementation must fail these tests. Full native candidate and post-merge public-source controllers must verify CDP, noVNC, pixels, pointer input and independent cleanup.

## Acceptance criteria

- Focused regressions, template/document checks and current-head CI pass.
- Actual candidate full-controller run and public-source rerun pass at their exact revisions.
- Historical failures and their cleanup remain recorded; no pass is inferred from unit tests.
