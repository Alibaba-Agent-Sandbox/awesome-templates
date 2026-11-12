# Verification: document engine package pins

Date:2026-11-12
Result:PARTIAL
Baseline:a34a709

## Triage and primary metadata

Existing Issue304 is reproduced by the current PR306 document-tools-offline
job before checkout (apt exits100 for u8). Official HTTPS Debian trixie amd64
Packages.xz advertises u6; trixie-security advertises exact u9 for all of
libreoffice-writer-nogui, libreoffice-core-nogui and libreoffice-common.
Pandoc/data and font versions remain available unchanged. Metadata was read
without credentials or cloud access.

## Scope

Update the CI and real recipe/runtime/smoke pins together, template1.1.3, docs
and design. Historical provider receipts are untouched. The existing exact
package, upstream binary and independent DOCX/PPTX/PDF/HTTP checks remain.

## Verification boundary

This operator has no Docker executable; mandatory real Debian-container tests
and image checks will execute using the existing GitHub workflows, not mocks.
No cloud resource or model task is created. Local and remote results follow.

## Local preliminary checks

Spec suite, full catalog and234-document link checks passed. The first scoped
run could not import the server because the pre-existing operator venv only
contained the client. A fresh task venv installed the exact CI server/client
0.4.0a6 and test dependencies. That run reported47 passed,14 failed and one
skipped because native Pandoc/Writer were not installed on the operator. These
are prerequisite failures, retained separately from the actual native run.
The host is Debian13; install the same exact native packages and rerun with
E2E_REQUIRE_DOCUMENT=1 before claiming native success.
