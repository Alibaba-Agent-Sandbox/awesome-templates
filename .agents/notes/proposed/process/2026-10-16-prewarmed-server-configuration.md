# Decision: Document process-start configuration for prewarmed named servers

Status: proposed

## Problem

Shared instructions describe create-time environment values as sufficient to configure a named-command server. An actual Express image review found its existing server did not expose all required settings after create-time injection. The model configuration guard refused the call. A new explicitly configured process from the same unchanged image subsequently passed setup through SDK, CLI and HTTP, then all 21 real-model checks. Existing process environment is a different lifecycle from sandbox creation.

Issue: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/93
Source acceptance: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/88

## Decision

Add a shared English/Chinese guide describing the observed boundary, a complete explicit process-start example, consistent port selection, stream consumption and owned sandbox cleanup. Qualify all existing quick starts and the reusable skeleton. Correct the specification's environment/authentication wording and its obsolete Python hello startup example. Replace conflicting legacy Claude/Codex usage pages with links to the maintained bilingual template contracts.

The guide distinguishes a new configured process from an old service, provider gateway auth from server auth, and model credentials from both. It does not claim authentication can be added to a prewarmed service by a later create call. It does not alter product code, source images, provider evidence or catalog qualification.

## API Design

Existing APIs only: Sandbox.create, commands.start(env=...), async stream consumption, network.get_url, run(server_port=...), server_at(token=...), kill and CLI --server-port. No endpoint, command name or configuration variable is introduced.

## Alternatives considered

- Repeating create-time env examples without qualification reproduces the observed setup failure.
- Replacing or killing an existing provider process assumes ownership and startup semantics that the review did not establish.
- Duplicating a full guide in every README creates inconsistent recipes; all quick starts link to one bilingual guide instead.

## Dependencies

The paired Python client/server and installed template commands. The observed image acceptance uses server source e2cb27e and Aider commands ecbabaf. The displayed Qwen example illustrates the same process API; it is not a new claim of Qwen image-backed model acceptance.

## Test Strategy

Run strict template conformance, the existing specification tests, changed-document relative-link checks, Python example compilation, secret/whitespace scans and a product-file diff check. Reuse the already completed real Aider image test without rerunning cloud jobs merely to validate prose.

## Acceptance criteria

- English/Chinese process-start instructions and qualified README examples agree.
- No claim that a new process changes the existing service's configuration or authentication.
- Existing canonical deployment and model acceptance boundaries remain explicit.
- Documentation and record checks pass; source/runtime files remain unchanged.

## Evidence

[Verification](../../../evidence/verify/2026-10-16-prewarmed-server-configuration.md).
