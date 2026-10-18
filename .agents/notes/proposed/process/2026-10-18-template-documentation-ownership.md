# Decision: Consolidate template setup and retire the unused registry copy
Status: proposed

## Problem

Template READMEs contain all three calling interfaces, but several installation
paragraphs assume unpublished packages. An unused copied registry page/data pair
contains stale provider claims despite the independent registry owning ingestion
and the website owning shared UI.

## Decision

Reuse the paired source-install guide with accepted SDK source 145341d; add a
bilingual usage entry covering CLI setup, direct POST shape/auth, SDK calls,
cleanup and evidence boundaries. Link existing READMEs instead of repeating
inconsistent install recipes. Remove the unconsumed registry/index.html and
registry/catalog.json pair; document the maintained registry owner and public
catalog migration. No template runtime, YAML, badge or evidence is changed.

## API Design

No runtime API changes. Readers of the retired local page/data must migrate to
the maintained registry; awesome-templates.yaml remains the source catalog.

## Alternatives considered

- Keep copied frontend/data: provider claims keep drifting from source owners.
- Add another source-install document: duplicates pins and lockstep caveats.
- Mark green image jobs as provider passes: violates version/tier acceptance.

## Dependencies

https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/82 owns the
current template contract correction and remains this documentation PR's base.
https://github.com/Alibaba-Agent-Sandbox/registry consumes awesome-templates.yaml.
https://github.com/Alibaba-Agent-Sandbox/website owns shared UI. No executable
consumer of the retired local registry pair was found in these repositories.

## Test Strategy

Check every template has CLI/SDK/HTTP sections in both languages. Re-run spec
unit tests, all-template checker and relative-link/record checks. Verify diff
leaves runtime, template YAML and historical evidence unchanged. Record public
package HTTP status by date, not an inferred publication promise.

## Acceptance criteria

- Existing paired source setup is linked from affected install paragraphs.
- Bilingual usage/ownership guide is reachable from the root README.
- No stale local registry implementation/data or dangling current link remains.
- Docs/spec/record checks pass; no cloud/provider badge is invented.
