# Decision: Exercise documented application transport through OpenSandbox

Status: proposed

## Problem
Actual OpenSandbox proxy requests dropped Bearer authentication. After that was
adapted, bodyless application DELETE became chunked and failed the bounded
server's framing contract. Public Python0.4.0a6/standalone0.5.7 also returned a
generic exception carrying stable E2009 after successful sandbox deletion.

## Decision
Run unchanged standalone HTTP controllers through a request adapter that mirrors
the documented application-token fallback, only for the selected service and
an already correct Bearer token. Preserve gateway headers and negative controls.
Frame only bodyless DELETE without explicit framing as Content-Length:0. Keep
server limits and source/runtime files unchanged. Recognize stable E2009 for
cleanup, independently polling absence after delete; other errors still fail.
Bind controller/adapter hashes before execution and reject changed inputs.

## API Design
New scripts/template_controller_transport.py wraps synchronous HTTP controller
clients. run_controller records its immutable input hashes and unchanged-input
check. The public runner's cleanup consumes the stable error-code contract; it
does not fix or claim corrected published SDK exception classes. Default model
isolation and explicit --real-usage behavior remain unchanged.

## Alternatives considered
Disabling authentication, overwriting gateway credentials, anonymous retry,
accepting chunked bodies without server bounds, or inferring cleanup from a
successful DELETE would weaken actual contracts. Editing every template's HTTP
controller is unnecessary when the documented transport already supports the
correct credential and framing.

## Dependencies
Refs https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/244;
fixes scoped controller defects247,248,249 after current-head gates pass.
Related https://github.com/Alibaba-Agent-Sandbox/registry/issues/70 and
https://github.com/Alibaba-Agent-Sandbox/blogs/issues/16.

## Test Strategy
Request-level regressions cover proxy stripping, negative credentials, exact
service scope, gateway preservation, body/encoding preservation and input changes.
Cleanup regressions require readback for stable E2009 and reject other codes.
Rerun the actual Docker-backed OpenSandbox with published CLI/Python and literal
README CLI/SDK/HTTP tasks; preserve both failed attempts and reconciliation.

## Acceptance criteria
Current-head checks and actual proxy workflow pass with independently confirmed
owned cleanup. Source evidence records five complete Express cases and the first
complete OpenSandbox case without promoting the remaining matrix. Registry
qualification and each practical article remain separate owner deliveries.
