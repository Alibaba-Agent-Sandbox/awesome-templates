# Decision: Correct confirmed documentation feedback

Status: proposed

## Problem

The root quick start recommends CLI 0.5.8 or newer while demonstrating source-only deploy/delete entry points, then describes cleanup as kill. Raw-ID cleanup also omits the named deployment’s ownership record.

## Decision

Link the existing source-installation instructions, distinguish published CLI 0.5.10 from the source command surface, and name the introductory deployment hello. Use its returned Sandbox ID for application calls and its local name for cleanup. Keep normal interactive confirmation and document retained images/borrowed artifacts. Align the shared guide in both languages.

## API Design

N/A — this decision does not involve API changes.

## Alternatives considered

Reverting to old launch/kill commands would undo the requested final CLI surface. Removing the minimum version without identifying source installation would still mislead users installing the current published package.

## Dependencies

Current CLI deploy and deployment_management command source at https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/tree/57c7632706aac739171fcdb7c2849938e58295ef. Template runtime, manifests and catalog remain unchanged.

## Test Strategy

Check changed Markdown links, bilingual wording, seven-section note structure and git diff hygiene. Use existing owner documentation gates where available. Runtime, image, deployment and model behavior are unchanged, so this prose correction does not require new cloud resources.

## Acceptance criteria

English and Chinese quick starts identify source installation, use one named deployment and accurate cleanup, and pass local document checks. Required remote gates pass before merge; no new cloud acceptance is claimed.

## Evidence

[Local documentation verification](../../../evidence/verify/2026-11-25-confirmed-documentation-feedback.md).
