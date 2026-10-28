# Decision: Recommend the published application-authentication release

Status: proposed

## Problem

The shared setup guide pinned CLI 0.5.7 after 0.5.8 published the clearer application-token guidance.

## Decision

Update only the English/Chinese shared template installation guide to CLI 0.5.8. Keep the Python
client pin, examples, catalog entries and template manifests unchanged. Move the accepted README
audience decision to implemented after its confirmed source PR merge; preserve historical evidence.

## API Design

N/A — this decision does not involve API changes.

## Alternatives considered

- Keep the earlier pin: rejected because current setup should include the released guidance fix.

## Dependencies

https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/releases/tag/v0.5.8.

## Test Strategy

Validate local Markdown targets and diff/record structure. Confirm official npm metadata/public
installation for 0.5.8 through the CLI owner's independent verification; do not claim runtime
coverage from these documentation checks.

## Acceptance criteria

- Both language guides name the same published CLI version and unchanged Python pin.
- Documentation links and record structure pass.
- No template/provider acceptance, catalog status or old evidence is changed.

## Evidence

- [Verification](../../../evidence/verify/2026-10-28-cli-058-template-installation.md)
