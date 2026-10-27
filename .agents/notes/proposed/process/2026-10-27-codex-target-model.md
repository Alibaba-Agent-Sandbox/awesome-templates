# Decision: Discover target Codex configuration without sharing model keys

Status: proposed

## Problem
A real required Codex launch passed14 smoke checks but refused/skipped model work
because its controller looked for model credentials on the host, where the public
runner intentionally does not put them.

## Decision
Read only codex_setup_check.api_key_present boolean flags on the target. Require
an actual configured target key for model work and retain explicit-off failures,
real source/artifact checks, independent original tests and held-out assertions.

## API Design
No runtime, manifest or public method change. Only the optional/required HTTP
controller's prerequisite changes from local secrets to remote diagnostic flags.

## Alternatives considered
Copying model credentials into the host controller, accepting a host-only key,
removing strict model requirements or accepting a skip would defeat isolation.

## Dependencies
Refs https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/244 and
https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/258. Public CLI0.5.7/client-server0.4.0a6.

## Test Strategy
A target-only key must reach actual source verification with no host key. A host
key with missing target configuration must stop before shell/model side effects.
Prove both regressions fail before correction. Keep tamper/held-out tests and run
the actual default Docker/Express model workflow with independent owned cleanup.

## Acceptance criteria
Regressions and real model run pass with no credential copied into the controller.
Complete newcomer documentation and public-method acceptance remain separate; no
Codex qualification follows from fixing this checker alone.
