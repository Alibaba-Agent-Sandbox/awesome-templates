# Decision: Pinned preview runtime
Status: proposed

## Problem

Issue54 needs actual frontend scaffolds and preview lifecycle beyond generic Node.

## Decision

Use integrity-locked Next16.4.2/React19.3.1/Vite8.3.4, fresh project creation and literal local CLI invocations. One owned persistent server with bounded logs and independent process/listener cleanup. Preserve caller project files.

## API Design

Six documented named commands. Existing directories and symlink/traversal paths rejected. SDK supplies provider URL from returned port. Buffered log tails, no claimed streaming or HMR certification.

## Alternatives considered

Unpinned create-next-app or runtime npm install introduces uncontrolled downloads. A static HTTP substitute would not verify Next/Vite. Docker/KVM are unnecessary.

## Dependencies

Existing source template spec/core acceptance PR121; official npm lock and Next/Vite docs. Node base observed20.20.2 satisfies upstream engines.

## Test Strategy

Actual two-framework preview requests and edit/readback, cleanup, unrelated listener preservation, source/path/overwrite failures. Strict docs/spec, image and real Express gates.

## Acceptance criteria

Genuine source/image/cloud results, owned cleanup, bilingual docs and ordinary reviewed merge. No issue closure before required gates.
