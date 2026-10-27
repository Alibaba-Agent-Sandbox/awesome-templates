# Decision: Require real browser work on the launched public application

Status: proposed

## Problem
browser-use and Stagehand required-use controllers always rejected model work and
referred to separate SDK controllers that start another command server. That cannot
certify the model settings and public application actually launched by a newcomer.

## Decision
Add host-side HTTP model controllers that create nonce browser fixtures inside the
owned sandbox, call the existing application, independently read actual page state
and download/validate PNG bytes. Preserve original native result validators and SDK
controllers. Never copy model/cloud credentials into host verification or fixture
environments. Keep explicit remote ownership and exact process identity cleanup.

## API Design
No runtime/public command changes. E2E_REQUIRE_LLM now requires actual configured
public browser operations. The general controller hashes additional verifier/
validator/fixture files before running and rejects any dependency changed afterward.
All existing authentication, no-skip and real usage requirements remain intact.

## Alternatives considered
A model success string, static screenshot, version-only pass or a second server
with different configuration cannot establish public application behavior.

## Dependencies
Fixes https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/264;
refs https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/244.
Existing pinned native packages, typed application endpoints, files/process API,
Pillow and original model validators are reused without new runtime dependencies.

## Test Strategy
Synthetic guard regressions require explicit ownership and reject claimed native
success when independent counter/receipt remains wrong. Compile guest verification
programs in tests; real subprocess cases reject mutated verifier dependencies.
Then pinned public default-Docker/Express launch with actual model and fresh literal
CLI/full SDK/HTTP examples, returned artifacts and independent owned cleanup.

## Acceptance criteria
Actual unchanged source and real business tasks pass, source CI passes, individual
articles and reviewed Registry qualification follow separately. Local synthetic
checks or pending cloud tasks cannot remove Beta or complete the full50 request.
