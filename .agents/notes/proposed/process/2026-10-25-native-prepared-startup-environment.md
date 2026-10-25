# Restore existing native startup environment compensation

Status: proposed

## Problem

PR229 forwarded explicit Dockerfile ENV to the prepared-reference manifest, but its public CLI0.5.6/SDK a6 agents control still failed. A same-instance diagnostic proved that binaries were installed and executable, ordinary creation environment markers and application authentication were inherited, while PATH remained the base value in default execution and the owned application. Explicit process environment restored binary lookup. The original failure is not an installation failure or evidence that all creation environment is lost.

## Decision

The existing production native-steps manager compensates for this platform behavior by wrapping startup and readiness with /usr/bin/env and the expanded explicit environment. The maintenance prepared-reference adapter bypassed that manager result. Restore that mechanism for its startup/readiness commands, using its existing merged environment and manifest priority. Omit empty declarations so inherited credentials remain dynamic. Build-only UV/cache/upload values remain excluded by the existing materializer.

## API Design

No public SDK, CLI, provider API, flag, template command or template version changes. Only the existing maintenance helper with a supplied runtime_env mapping wraps original startup/readiness; image consumers using runtime_env=None preserve their original commands. Shell quoting preserves literal values and original command semantics.

This restores application startup compensation for this adapter. It does not fix or certify general PATH inheritance for arbitrary public prepared-reference creation or SDK processes, and does not settle the separate production-wrapper collision-priority question. The adapter keeps its previously documented manifest priority; the production wrapper gathers Docker ENV directly.

## Alternatives considered

Forwarding manifest ENV alone was insufficient, as the preserved PR229 public control demonstrates. Changing business commands or binaries would conceal the transport behavior. Starting a sibling server, adding another runner, changing global PATH or publishing another SDK/CLI version is unnecessary for this adapter correction.

## Dependencies

https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/227

https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/229

Existing production mechanism: https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/blob/1ea3eabd679c3cf26c824492a60fe2a8aea43f62/src/template/build_plan.ts#L23

## Test Strategy

A real subprocess installs a fixture tool outside the base PATH, then executes original startup and readiness. It verifies environment restoration, manifest priority, literal quoting and inherited empty-secret declarations without embedding their values. Keep the image path unchanged. Preserve the failed public control and the filtered same-instance diagnostic. Independently review the candidate and run the existing full agents control before accepting it.

## Acceptance criteria

The real subprocess regression fails against public4229 and passes with the correction. Relevant latest-head CI and independent reviews pass. A candidate cloud control completes its existing controller and independently confirms sandbox/template absence. Public main remains frozen until the already running OpenSandbox matrix finishes; final native supplemental acceptance follows normal merge. Default Express Docker acceptance remains separately BLOCKED.
