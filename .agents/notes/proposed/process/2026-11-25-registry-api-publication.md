# Decision: Validate optional Registry API bindings

Status: proposed
Date: 2026-11-25
Issue: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/317

## Problem

The CLI already binds registry.apis to an existing Sandbox, while the template schema lacks the field and the active checker ignores it. Publication can therefore accept a declaration which cannot be loaded.

## Decision

Add an API-bindings fragment to the existing Registry schema and a canonical publication validator. The active checker checks optional metadata without activating the separate v1 resource engine. Keep package containment, bounded Core YAML, internal references and operation identity checks aligned with the CLI. Publish only identity summaries.

## API Design

registry.apis maps API names to resource, port and openapi. The current resource grammar is sandbox.NAME. Local aliases and credential references belong to the CLI binding. No Serving binding, automatic signer, dynamic download or x-abx invocation extension is introduced.

## Alternatives considered

Do not create a second full schema, duplicate the invocation engine, force publication fields onto local API-only metadata, or merge an unverified v1 migration to fix this publication gap.

## Dependencies

Uses the existing YAML Core reader and pinned checker dependencies. Registry consumes this canonical validator. CLI request/authentication validation remains authoritative; structural acceptance does not assert reachability, permission or cloud qualification.

## Test Strategy

Exercise the real filesystem/parser/schema/checker for valid metadata, invalid ports/resources, external and recursive refs, symlink escape, duplicate operations, unsupported extensions and harmless literal example values. Run the full spec/checker/docs gates.

## Acceptance criteria

Optional API declarations have a supported producer contract; invalid declarations fail before catalog publication. Existing catalog templates still conform. English and Chinese docs distinguish current bindings from unmerged resource design.
