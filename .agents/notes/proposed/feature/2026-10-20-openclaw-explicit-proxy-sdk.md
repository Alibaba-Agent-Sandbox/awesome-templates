# Decision: Explicit gateway proxies and real SDK acceptance

Status: proposed

## Problem

[Issue20](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/20) requires useful native gateway/ports/headless operation and actual SDK Express acceptance. Current2.0.1 actual gateway auth RPC and public forwarded healthz pass, but forwarded readiness returns403. The pinned upstream rejects unattributed forwarded headers; basic stopped-status/version smoke cannot detect it. A first controller also confused ready=true with the distinct liveness ok=true schema.

## Decision

Add bounded explicit operator OPENCLAW_TRUSTED_PROXIES to the isolated native gateway config in2.1.0. Preserve upstream auth/proxy policy, default loopback and caller configuration. Do not trust request header values or the whole Internet. Add a reproducible borrowed-sandbox SDK controller: independently observe an owned nonce probe's kernel peer, explicitly configure that exact test address, start/authenticate/check/stop the actual native gateway and verify external liveness/readiness plus own listeners/state absence. An owned ephemeral probe exits naturally; no unknown process is killed.

## API Design

Existing named commands/defaults and return fields remain. The optional process-start environment accepts at most16comma-separated IPs/CIDRs and2048UTF-8 bytes, canonicalizes/deduplicates, rejects malformed/empty/unrestricted/multicast networks. Empty preserves upstream defaults. The CLI verification uses the SDK controller without secrets in argv. The Python example explicitly starts an authenticated9010command server. The controller borrows a fresh sandbox and owns only9010/9012/18789processes and native private state; caller owns final sandbox deletion. Gateway-only scope requires no model key.

## Alternatives considered

Trusting forwarded header contents or0.0.0.0/0 would bypass attribution. Treating healthz alone as full readiness hides the observed403. A provider name does not prove a trusted source CIDR; operator settings remain explicit. Reusing caller processes/profiles or killing an occupied port violates ownership. Using a one-request probe consumed by unrelated readiness traffic, or killing only its shell without listener verification, caused failed diagnostics; those cloud attempts remain unqualified and independently cleaned up.

## Dependencies

Unchanged OpenClaw2026.10.4, Node24.16.0/hash pins and existing SDK/server paths. Native [probe contracts](https://github.com/openclaw/openclaw/blob/v2026.10.4/src/gateway/server-http-probes.ts) distinguish ok from ready. Native [HTTP routing](https://github.com/openclaw/openclaw/blob/v2026.10.4/src/gateway/server-http.ts) rejects unattributed proxies before readiness/business routing. No new product package/model/backend.

## Test Strategy

Actual authored process cleanup tests plus config materialization regression prove exact proxy settings enter the owned native config and the state is removed. Bad proxy input must fail before Popen. Controller regressions reject wrong readiness schema, status, booleans and HTML errors. Current2.1image/steps must actually run SDK auth lifecycle, external healthz/readyz and independent cleanup. Record all prior failures without relabeling them.

## Acceptance criteria

Source/process/controller/strict/docs gates pass; current-head actual L1 and mandatory CI pass; real2.1SDK-created image and native steps validate useful authenticated gateway/external probes and independent owned sandbox/template/registry cleanup. Bilingual contracts and current qualification agree. Normal scoped PR merges and Issue20closes only after those gates. No model/channel claim is inferred.

## Evidence

[Verification](../../../evidence/verify/2026-10-20-openclaw-explicit-proxy-sdk.md).
