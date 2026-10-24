# Source application quick starts

Status: proposed

## Problem

The 46 source-template README pairs and `_skeleton` repeat create-based examples
that neither own application startup nor bind its token/gateway correctly.
Qwen additionally advertises a long CLI model call although CLI 0.4.16 application
requests have a fixed 30-second wait. Issue: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/208.

## Decision

Use the existing shared bilingual launch/connect/HTTP guide as the single setup
explanation. Each README keeps its actual first manifest smoke command, argument
object and result envelope. Preserve business command references and historical
receipts. Qwen retains complete keyless examples plus separately configured model
usage through clients with explicit waits. Remove obsolete current requalification
introductions and describe the application workflow's required independent token.

## API Design

No runtime, image, manifest, catalog, command signature, SDK or CLI API changes.
`template launch` owns startup; Python connects and binds `application_client`;
HTTP preserves resolved gateway headers and URL scope. No new state or generator.
Documentation-only source tree digests change; the separate 92-case run remains
bound to its original ba17fbd/e581 inputs and does not certify these new digests.

## Alternatives considered

Fixing Qwen alone leaves all other active quick starts wrong. Copying complete
authentication implementations into 47 pairs perpetuates drift. Mechanical
`sb.run` replacement can confuse process calls, application calls and deadlines.

## Dependencies

Published CLI 0.4.16 and Python client 0.3.1a5; existing template-pinned server
source remains unchanged. The shared guide owns installation and provider setup.
Managed-reference docs are a separate change in
https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/207.

## Test Strategy

Strict all-template checker, documentation links, Python snippet parsing, actual
manifest argument comparison, unchanged-runtime diff, targeted existing Qwen tests
and required CI. Repeat Qwen's installed-client Express launch, version/setup
through CLI/Python/HTTP and independent owned cleanup using the existing harness.
Model usage is not a real-model pass. Keep failed attempts and missing checks.

## Acceptance criteria

- Bilingual active quick starts follow the explicit application path.
- Business contracts and historical evidence remain scoped and intact.
- Local checks, exact-head CI and cross-review pass.
- Qwen keyless public entry and owned cleanup have a separate actual receipt.
- Merge through the normal PR workflow; full matrix stays in Issue203.
