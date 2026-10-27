# Decision: require a cookie-preserving endpoint for the actual browser IDE

Status: proposed

## Problem
OpenSandbox server-proxy mode passes the original five grouped native checks but
fresh real browser editing fails with workbench connection timeout. The lightweight
external assertion can mistake a login page containing workbench for success.
Official server1.1.1 filters Cookie from HTTP and WebSocket forwarding.

## Decision
Strengthen the original external controller to reject a final login URL or password
form. Add a false-positive regression and run it in CI. Document the existing
provider direct-endpoint mode, requiring caller reachability and native password/
cookie authentication, rather than claiming the cookie-stripping proxy works.
Increment template to1.0.3 and retain original failed real usage as evidence.

## API Design
Public named methods/lifecycle unchanged; no authentication, certificate or local
preview isolation relaxation. Use ABX_OPENSANDBOX_USE_SERVER_PROXY=false before
launch and for later clients. The existing SDK resolves the actual endpoint.

## Alternatives considered
A displayed workbench shell or CLI-only pass is insufficient. Disabling password
or cookie authentication, editing the foreign installed server, or inferring
provider support without actual editor/save/file results would be incorrect.

## Dependencies
Refs https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/280 and
https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/244.
Provider default direct mode already exists; no provider/SDK package changes.
Fresh current-source Express and direct OpenSandbox evidence and Registry review
are required. Existing recorded Express source remains historical.

## Test Strategy
An explicit HTTP fixture strips the session cookie and returns a login document
mentioning workbench. Original controller incorrectly passes; regression fails
before fix and rejects it after, while authenticated session passes. Both paths
confirm owned stop. Fresh full actual browser edit/save/independent source execution,
all native/method/documentation use and owned cleanup on both providers remain.

## Acceptance criteria
Local scoped checks, final-head CI with correct pinned native IDE, real current
Express/direct OpenSandbox full use, Registry receipts and published documentation.
No default server-proxy IDE qualification or full50 completion claim.

Fresh actual Express/OpenSandbox workflows are now complete: see the dated evidence
and per-provider JSON. Template folder trees match immutable combined source4c4d1a7.
Registry receipts, practical article updates and public readback remain required.
