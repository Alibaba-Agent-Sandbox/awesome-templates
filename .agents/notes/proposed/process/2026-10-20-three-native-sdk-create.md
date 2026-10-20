# Decision: complete native SDK creation for three reviewed coding profiles

Status: proposed

## Problem

Issues28/41/50 need actual Python Sandbox.create after official READY. Prior current Hermes/Pi/Aider images and real-model receipts used CLI-created sandboxes with native SDK connect; SDK use does not itself prove SDK creation.

## Decision

Repeat actual verified-image registration/READY/native SDK creation, CLI/SDK commands, full model-off HTTP and independent owned sandbox/template/registry cleanup. Preserve every merged receipt. Reuse successful prior exact-version/commands/controller real Express model proof as a separate historical gate; no unnecessary repeat model call or new model pass claim.

## API Design

No template runtime or public API change. Actual native Sandbox.create route is selected by the already-reviewed harness flag. New immutable dated receipts and bilingual verification text identify that route and separate model-off SKIPs.

## Alternatives considered

A mocked factory or CLI-created Sandbox.connect cannot establish native creation. Overwriting same-day merged receipts would lose history. Source/controller SHA256 equality and prior actual model evidence permit explicit provenance reuse without pretending this new run invoked a model.

## Dependencies

Unchanged reviewed Hermes1.1.1, Pi1.0.1 and Aider1.0.1 CI images, fixed SDK client/server and native CLI. Provider/registry credentials stay private; no runtime dependency or model endpoint change.

## Test Strategy

Actual registration/official READY/SDK creation/CLI and SDK named smoke/full model-off HTTP. Exact-version/runtime/controller checks against prior successful real-model receipts. Independent owned cloud absence and pre/post digest readback, new immutable files. Strict source/docs/current-head CI before normal merge.

## Acceptance criteria

All three actual native creation and owned cleanup passes, unchanged prior real-model evidence explicitly distinguished, complete bilingual documentation, source/docs gates and normal merged PR; only then close original Issues28/41/50.
