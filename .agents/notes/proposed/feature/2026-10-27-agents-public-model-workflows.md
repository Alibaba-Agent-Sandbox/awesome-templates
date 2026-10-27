# Decision: Complete public Agents CLI model setup

Status: proposed

## Problem
The launched restricted application lacks explicit native Codex profile preparation;
older model acceptance starts a different9010 server. Public core omits native turns.
The optional standalone SDK verifier also references undefined Sandbox (Issue241).

## Decision
Add explicit agents_configure_codex, using startup endpoint and environment key
reference, native Responses and WebSockets disabled. Exclusive0600 creation, matching
config idempotence, foreign/symlink config preservation. Require both native adapters
and two-turn continuation on the original public9000 application, independently
checking files/native persisted turns through host provider management APIs.
Fix the old verifier's default factory with a lazy published ProviderSandbox import.

## API Design
Template2.1.0 adds one named preparation command. Existing six session/runtime routes
and closed file/shell/process HTTP policy remain. No model key enters a controller,
no second command server and no implicit preparation on import/version inspection.
Both README languages explain API-key login, protocols, model/key/endpoint changes,
real tasks, SDK downloads, native continuation and exact cleanup.

## Alternatives considered
A session create/version is not model work; assistant output is not independent
artifact verification. Generic HTTP policy expansion would change the scoped product.

## Dependencies
https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/271 and
https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/241. Broad Issue244
and the50-article series remain open. Pinned native CLIs/server unchanged.

## Test Strategy
53 setup/policy/protocol/verifier regressions; exact native config/no key-file,
foreign config preservation; actual public model turns on both adapters plus host
independent generated code/session state; literal documented consumers, second
startup model, specification/docs/secret/diff checks and current-head CI.

## Acceptance criteria
Actual all methods/routes, native coding/continuation and independent file/state
verification, complete article, reviewed Registry qualification and public delivery.
Pending actual cloud run does not qualify this template.
