# Start the complete template without workflow selection
Status: proposed

## Problem

Source templates duplicate their startup, application protocol and operations in a named workflow. Users must understand a path selector even though all 46 default source recipes expose the same command service. Managed catalog entries also repeat an identical execution workflow instead of describing their native identity.

## Decision

Use specification 5 with the existing startup/readiness commands and all provided services. Remove author-written workflow contract version, workflow maps and default selectors from 46 sources, the skeleton, both application-deployment examples and four managed entries. Preserve every runtime recipe, command handler, provided operation and native provider identity. Reject old runtime manifests with an explicit migration message. Historical evidence is immutable and is not promoted to new-format acceptance.

## API Design

`abx --provider <provider> template launch <reference>` starts the template once. Consumers prepare source as needed, create a sandbox, run `start_cmd` and check readiness and every declared service. Business commands requiring a password, prompt, dataset or directory remain explicitly callable after startup. Application deployment hooks stay outside sandbox launch. The catalog, source checker and public launch harness no longer require or supply a workflow selector.

## Alternatives considered

Merely hiding the default CLI flag retains the redundant author contract and multiple contradictory planning inputs. Automatically selecting an old workflow would silently discard alternatives and leave ambiguous compatibility. Executing every registered business command during startup would invent inputs and cause unintended side effects.

## Dependencies

- [Template Issue](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/212).
- [Canonical launch contract owner](https://github.com/Alibaba-Agent-Sandbox/python-sdk/tree/main/contracts).
- [CLI consumer](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox).
- [Registry consumer](https://github.com/Alibaba-Agent-Sandbox/registry).

CLI 0.4.17 predates specification 5. Consumers and published installation guidance must be aligned before these manifests are advertised as directly usable.

## Test Strategy

Run checker and schema regressions, multi-service and retired-schema cases, all catalog validation, public launch harness regressions, historical/current contract lock checks and documentation links. Compare all runtime/startup fields with the base revision. Real provider validation uses the revised public launch harness and exact consumer revisions; old cloud receipts do not satisfy this gate.

## Acceptance criteria

The source catalog and managed references contain no workflow selectors; required local and CI gates pass; CLI/SDK/registry consumers support the same contract; representative and required cloud acceptance has exact provenance and independent cleanup; installation guidance names usable artifacts; each owner PR is merged after its gates pass. Until those cross-repository gates complete, this decision remains proposed.
