# Decision: Publish the managed manifest contract independently

Status: proposed

## Problem

The managed Agents template and its new manifest contract share one feature branch. The deployment
CLI must consume an accepted producer contract, while the final public template requires published
compatible CLI and SDK packages. Delivering these as one indivisible change creates a release-order
cycle and can imply that an unverified recipe is already usable.

## Decision

Extract the exact reviewed schema and static validation from the template branch into an independent
producer PR for [Issue298](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/298).
Preserve schema SHA-256 `3cce2cfc36a284ee2e84bce977bd22090b9419e991a5371854c96e74d12ec479`
and every spec5 contract. Add bilingual normative reference and contributor guidance, with independent
temporary manifest fixtures. The legacy local named-command runner explicitly rejects the new managed
startup profile before preparing imports, ports or processes. It does not gain managed runtime support.

Do not include the agents-api directory, catalog declaration, image/acceptance CI modifications,
public API business guide, or unpublished dependency pins. Runtime, recipe, model/provider acceptance
and catalog publication remain separate deliveries. The independent acceptance reviewer approved
this boundary and the fail-closed legacy-runner guard before implementation.

## API Design

The producer exports `spec/template-v6.schema.json`, `validate_v6`, `validate_manifest`, and
`is_managed_application`. Version 6 selects only the explicit closed managed bridge application;
version 5 retains its prior startup and application semantics. Validation never executes hooks,
installs SDKs or deploys resources. The legacy runner returns a controlled unsupported-profile
failure instead of starting commands.py for a managed manifest.

## Alternatives considered

- **Merge the whole template first**: rejected because public recipe acceptance still depends on
  unpublished compatible packages and would temporarily expose an unusable catalog entry.
- **Publish consumers before their contract**: rejected because shared contracts land first.
- **Add source installation fallback**: rejected because source acceptance is a separate gate.
- **Start commands.py for the new profile**: rejected because diagnostic startup is not the declared bridge.

## Dependencies

The existing pinned checker dependencies only. Contract bytes originate at reviewed producer commit
`6c0bd346d94ed888d3c2674309d73e13474363a6`. Related complete template delivery is
[PR296](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/296); consumers are
[CLI PR235](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/pull/235) and
[Registry PR92](https://github.com/Alibaba-Agent-Sandbox/registry/pull/92). SDK runtime delivery is
[PR156](https://github.com/Alibaba-Agent-Sandbox/python-sdk/pull/156), with no import dependency
on this static producer.

## Test Strategy

Run independent temporary legal/illegal manifests through both the schema/semantic validator and
complete directory checker. Cover topology, role/secret boundaries, finite budgets, frozen Server
inputs, source containment, legacy rejection before process preparation, and existing spec5 behavior.
Run full specification/catalog/documentation checks and current-head CI. No SDK module, template
image, cloud credential or model is needed to prove these static contracts.

## Acceptance criteria

- The exact reviewed v6 schema is available without publishing an executable template.
- Existing v5 manifests and checker behavior remain valid.
- Managed manifests receive strict independent positive/negative checker tests.
- The legacy commands-only runner cannot report a managed bridge pass.
- Required local and remote gates pass; no runtime/provider/model qualification is inferred.
- The scoped producer PR merges before deployment consumers; Issue295 remains open.
