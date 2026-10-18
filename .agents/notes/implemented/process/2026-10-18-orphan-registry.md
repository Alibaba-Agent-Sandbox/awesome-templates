# Decision: Retire the unused template-local registry snapshot
Status: implemented

## Problem

A legacy HTML/catalog JSON pair duplicates the independently maintained registry
and gives readers an obsolete site ownership/deployment path. Only that HTML
consumes its local JSON; the actual registry ingests awesome-templates.yaml.

## Decision

Delete registry/index.html and registry/catalog.json. Link the maintained registry
owner/site from the bilingual root ownership paragraph. No template runtime,
metadata version, tested_on badge or consumer API changes.

## API Design

No public template command or catalog schema change. The obsolete local static
HTML/JSON path is retired in favor of the maintained registry project.

## Alternatives considered

- Update both copies: retains duplicate ownership and stale output risk.
- Wait for all23 deployment gates: unrelated runtime gates need not hold a
  standalone documentation/artifact cleanup.

## Dependencies

https://github.com/Alibaba-Agent-Sandbox/registry owns the real site. This cleanup
is also present in the larger acceptance PR109; no runtime feature is landed here.
https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/109

## Test Strategy

Search source consumers in all eight owners, verify only the retired HTML reads
its JSON, inspect actual registry ingestion, run checker/spec/link/record checks
and required hosted CI. No cloud execution is needed for these dead artifacts.

## Acceptance criteria

- No executable consumer outside the deleted pair.
- Existing YAML catalog/template runtime/evidence bytes unchanged.
- Current site ownership and required checks documented accurately.
