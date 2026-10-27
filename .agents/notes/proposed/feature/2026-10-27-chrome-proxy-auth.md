# Decision: preserve Chrome application authentication through provider proxies

Status: proposed

## Problem
Actual OpenSandbox Chrome1.0.8 completes15 native assertions but CDP discovery
aborts with JSONDecodeError. The relay accepts only Authorization, which the
provider proxy strips. Native VNC challenge authentication is a separate boundary.

## Decision
Accept the explicit X-Access-Token application fallback only when Authorization
is absent. Retain direct Bearer support and reject an explicitly incorrect or
unsupported Authorization even if a correct fallback is present. Both HTTP and
WebSocket CDP handlers share this check. Send both app headers in the original
controller, update bilingual direct-CDP guidance, and increment Chrome to1.0.9.

## API Design
Named commands and response shapes unchanged. Add a compatible authentication
transport, not a new credential. Native VNC still requires its original generated
password. Gateway headers, resolved URL path/query and expected application token
remain separate. No credentials in URLs, browser pages or public evidence.

## Alternatives considered
Disabling CDP authentication or marking an image/health check as portability would
weaken the public contract. Wrong Bearer must not be rescued by a fallback header.
The actual provider failure is retained and fresh native use remains mandatory.

## Dependencies
Refs https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/278 and
https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/244.
No dependency/native browser changes. Registry needs new exact-source Express and
OpenSandbox receipts before current1.0.9 may qualify; old receipts remain history.

## Test Strategy
A real loopback proxy strips Authorization while retaining the explicit fallback:
regression fails401 before the fix and passes after; wrong/missing/unsupported
Bearer and wrong fallback still reject.27 Chrome unit/protocol tests pass.39 spec
tests, all-template checker and224-document link checker pass. Fresh full original
native/GUI/CLI/full SDK/direct HTTP on both providers and cleanup are still pending.

## Acceptance criteria
Current source must pass both actual provider workflows, all methods and actual
CDP/VNC/PNG browser tasks, owned cleanup, final-head CI/review, source/Registry/docs
publication. No full50 completion or current OpenSandbox qualification claim yet.

Fresh actual Express/OpenSandbox workflows are now complete: see the dated evidence
and per-provider JSON. Template folder trees match immutable combined source4c4d1a7.
Registry receipts, practical article updates and public readback remain required.
