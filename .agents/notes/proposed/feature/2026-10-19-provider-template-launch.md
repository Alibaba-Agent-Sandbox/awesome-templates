# Decision: Describe adapter-prepared template references
Status: proposed

## Problem

Catalog visitors are asked to supply provider template IDs or manually publish an image before trying source templates. References and build policies differ by backend.

## Decision

Replace preexisting-ID/push-image catalog hints with provider-prepared hints and document the source-to-preparation-to-sandbox workflow in English and Chinese. Keep PTY restrictions and all historical native acceptance claims.

## API Design

No template runtime or template.yaml schema changes. Optional catalog compatibility hints remain advisory; the selected provider capability declaration is authoritative.

## Alternatives considered

- Keep manual IDs as the primary path: this leaves the requested first-use workflow incomplete.
- Dispatch on known provider names in core or Registry: this couples consumers to backend policy.
- Claim capability parity or promote all providers: references cannot add missing PTY/code support and native acceptance is independent.

## Dependencies

Tracked by https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/118. Cross-repository delivery depends on https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues/69, https://github.com/Alibaba-Agent-Sandbox/awesome-providers/issues/16, https://github.com/Alibaba-Agent-Sandbox/registry/issues/13 and https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/118. The published CLI 0.4.0 predates launch; until a new release, users must build the reviewed source as documented.

## Test Strategy

python3 scripts/test_spec_tools.py: 36 passed. python3 scripts/check_template.py --all: 23 conformant, zero failures. Template Dockerfiles, runtime commands and provider acceptance evidence are unchanged; no unrelated cloud tests were run for these catalog/documentation edits.

## Acceptance criteria

- Selecting source does not require manually copying a backend ID when preparation is supported.
- Provider policy remains with its owner; unsupported capabilities fail before resources are prepared.
- Documentation lists one-time credentials/tool/image prerequisites and artifact costs/cleanup.
- Required CI passes on the current PR head; owner PRs are merged in dependency order.
- Registry deployment ingests merged revisions and production readback verifies the published result.

## Evidence

See [verification](../../../evidence/verify/2026-10-19-provider-template-launch.md). Proposal status is retained until acceptance gates have actually passed.
