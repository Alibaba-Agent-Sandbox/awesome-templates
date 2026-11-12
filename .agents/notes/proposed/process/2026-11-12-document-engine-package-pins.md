# Decision: Restore the pinned document engine packages

Status: proposed

## Problem

Issue304 blocks unrelated contributions before checkout: Debian trixie no longer
serves LibreOffice4:25.2.3-2+deb13u8. The same unavailable pin affects the actual
document-tools image, runtime exact-version check and declared smoke outputs.

## Decision

Pin writer-nogui/core-nogui/common to4:25.2.3-2+deb13u9 consistently in CI,
Dockerfile, runtime and smoke expectations. Bump template1.1.2 to1.1.3 and update
both README languages/design. Keep Pandoc/fonts/SDK versions unchanged and
retain all actual conversion, size, cleanup, SDK and external HTTP assertions.

## API Design

No conversion arguments/output contract change. office_version reports the new
exact package identity. Historical receipts remain byte-unchanged and do not
certify the changed recipe.

## Alternatives considered

Unpinning installs or skipping the gate would hide the failure. Selecting main's
u6 package would downgrade relative to the old security build. Debian-security
currently provides exact u9 for all three required packages; it preserves the
25.2.3 upstream binary family and needs current actual conversion/image checks.
Freezing an older archive would retain an obsolete security dependency.

## Dependencies

Official Debian trixie and trixie-security amd64 Packages.xz metadata, inspected
on2026-11-12. Refs https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/304.

## Test Strategy

Run specification/document checks and scoped regressions. Require the actual
Debian-container document suite (including SDK and external HTTP), local startup
smoke and actual Dockerfile L1 build/non-root/pinned smoke through existing CI.
No new provider qualification or cloud/model claim.

## Acceptance criteria

All three exact packages install, native office_version agrees, actual document
conversions and HTTP/SDK artifact checks pass, and the actual image builds and
runs its unchanged pin/smoke gates. No assertion weakened or history rewritten.

## Evidence

[Verification](../../../evidence/verify/2026-11-12-document-engine-package-pins.md).
