# Native SDK entry for host acceptance controllers

Status: proposed

## Problem

The root Python `Sandbox` now follows the standard synchronous contract. Host acceptance controllers still awaited its lifecycle methods and named server calls. The doc migration alone did not update these executable consumers.

## Decision

Select `agent_sandbox.api.sandbox.Sandbox` explicitly in Express runtime, named-command, inventory/recovery and agents-cli verifier controllers. Update the skeleton explanation and remove the obsolete sync-factory defect claim. Keep runtime images and provider acceptance badges unchanged.

## API Design

No public API changes. Host controllers await native lifecycle and named commands; borrowed clients are closed without destroying sandboxes.

## Alternatives considered

Using root AsyncSandbox would preserve asynchronous syntax but would select the standard shell API rather than native named server commands. Changing production images is unnecessary for selecting the host client.

## Dependencies

- https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/116
- https://github.com/Alibaba-Agent-Sandbox/python-sdk/pull/47
- https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/115

## Test Strategy

Use distinct standard/native doubles to reproduce wrong API selection and verify argument forwarding and borrowed-client close. Run cleanup/recovery, agents-cli verifier/protocol, spec/checker and offline local acceptance checks. Keep optional live probe failures separate from local regression passes.

## Acceptance criteria

- Controllers select native async lifecycle and named-command APIs.
- Wrong root selection fails the regression; corrected entry passes.
- Cleanup/recovery and verifier checks pass.
- Latest-head required CI passes before normal merge; no cloud/model Actions or provider badge promotion.
