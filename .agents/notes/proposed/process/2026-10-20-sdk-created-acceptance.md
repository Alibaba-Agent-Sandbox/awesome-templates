# Decision: record actual SDK sandbox creation in acceptance

Status: proposed

## Problem

[Delivery Issue119](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/119) includes template Issues that explicitly require Python SDK `Sandbox.create`. Existing canonical runs use CLI creation followed by SDK named commands; those facts do not establish the Python creation call.

## Decision

Add an explicit `--sandbox-create cli|sdk` selector to the canonical, step and verified-image runners. Preserve CLI as the compatible default. Record the selected actual operation in new receipts and keep historical evidence immutable.

## API Design

After official READY, SDK mode invokes the native asynchronous Sandbox.create with the owned template ID and sandbox lifetime. Return its known ID to the existing private journal and close only the local client. Continue CLI/SDK command smoke and existing CLI destruction plus independent ownership/readback checks. A local close failure cannot hide an already-created ID. A failed creation response remains ambiguous and must use existing exact-template recovery; no failed response publishes a pass.

## Alternatives considered

Do not relabel CLI creation as a Python SDK call. A second unjournaled helper sandbox complicates ownership unnecessarily. This changes only controller creation selection, not a template image/runtime or the actual SDK contract.

## Dependencies

Reviewed native Python SDK API, existing credential configuration, unique owned template journals and native CLI cleanup/readback. No cloud/model secrets enter CI. Consumer integration follows the workspace ownership source branch.

## Test Strategy

Demonstrate the missing selector before the change. Verify route dispatch, actual SDK argument plumbing, client close, known-ID preservation after close failure, unchanged CLI/SDK smoke and owned cleanup, and ambiguous creation failure with no receipt. Run the established controller/materializer suites and separately execute real image/model acceptance using the new SDK route.

## Acceptance criteria

- The opt-in operation actually uses Sandbox.create; receipts identify it honestly.
- Existing default CLI behavior and all ownership/cleanup/no-false-pass gates remain.
- Focused and current-head CI pass; genuine SDK-created cloud acceptance is recorded separately from fixtures.
- Both guides/languages and indexed engineering records are complete; normal merge/readback follows the source dependency.
