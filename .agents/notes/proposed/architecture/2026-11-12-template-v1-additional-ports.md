# Decision: Preserve additional access ports without inventing services

Status: proposed

## Problem

Original manifests contain real additional access ports absent from their versioned service
contracts. Dropping the separate declaration loses ports in seven templates. Fabricating
protocol names or versions for on-demand listeners would invent a service promise.

## Decision

Add optional sandbox.ports as unique integer access ports1..65535. Private compilation returns
the sorted union with services.port. Keep services as the genuine business protocol contract.
Managed bridge and Gateway routing stay unchanged; additional ports do not publish Gateway APIs.

## Alternatives considered

Port-only services require changing typed client contracts for unrelated listeners. Fabricated
protocol/version fields misdescribe on-demand services. Dropping raw ports loses existing use.
An optional extra-port list is the smallest declaration matching the original behavior.

## Dependencies

Independent CLI and SDK reviews select the same minimal approach. Both consumers must preserve
the union through their private model. Tracker: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/309.

## Test Strategy

Actual shared schemas and both pure compilers check raw-only and union cases. Reject bool,
zero,65536 and duplicates. Migration separately compares all48 original port sets and only
writes raw ports not already represented by a real service.

## Risks and Limitations

An exposed port proves neither readiness, HTTP, authentication nor listener implementation.
No new cloud port mapping or Managed public route is implemented by this producer change.

## Rollback Plan

Revert with coordinated consumer locks and retain original declarations. Do not silently
drop additional ports from migrated templates or rewrite old receipts.
