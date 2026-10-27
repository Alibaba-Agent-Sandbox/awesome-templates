# Decision: preserve provider resolution and complete additional practical cases

Status: proposed

## Problem
The local preview utility calls synchronous network.get_url, which cannot represent
OpenSandbox server-proxy gateway headers. The native browser concurrency verifier
uses module-level httpx convenience calls that retain the original Client class;
replacing the exported class does not attach scoped application authentication.

## Decision
Use the public asynchronous network.resolve result and preserve its gateway headers
for HTTP and WebSockets. Allow explicit HTTP only for a literal loopback SDK
endpoint. Attach controller authentication through the public Client constructor,
covering both convenience calls and explicit clients without weakening scope checks.
Preserve five completed OpenSandbox experiences and the two original failures.
Record Claude/Gemini explicit compatible-mode use separately from whole-template
qualification; unverified native vendor commands retain Beta.

## API Design
PreviewRelay gains optional gateway_headers and allow_loopback_http; existing
HTTPS callers remain compatible. sdk_preview awaits network.resolve. Browser
headers cannot override SDK gateway authentication. Next-app1.1.4 also adds only the exact127.0.0.1 development origin to new Next
scaffolds; actual logs confirmed native Next blocked relay HMR. No wildcard origins,
new command servers, credentials, management-key preparation or CI secrets.

## Alternatives considered
A health response, replacing the concurrent browser assertion, or silently using a
header-free endpoint would not establish the documented behavior. A compatible
model key does not authorize native vendor endpoints. Original failures remain.

## Dependencies
Refs https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/244 and
https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/275, and
https://github.com/Alibaba-Agent-Sandbox/blogs/issues/16. Published CLI0.5.7 and
Python client/server0.4.0a6. Provider-owned resolution remains in the SDK/provider.

## Test Strategy
Actual HTTP/WS SDK-resolution regression; constructor/concurrent positive auth,
wrong-token and other-path controls. Repeat real OpenSandbox browser and Next.js
use and Express Next.js preview. Exact source identities, literal CLI/full SDK/
HTTP business tasks, independently read outputs and owned cleanup. Run required
specification/docs checks and configured-secret scan. Keep failures separate.

## Acceptance criteria
Current-head CI/review, source receipts, practical articles, separately reviewed
Registry provider receipts and public readback. No whole-template qualification
for compatible-only Claude/Gemini use. Broad50-template delivery remains incomplete.
