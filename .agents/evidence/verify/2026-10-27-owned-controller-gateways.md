# Owned Docker gateway controller targets

Result: PARTIAL (local ownership regression passes; actual reruns required)

Date2026-10-27. Original Copilot OpenSandbox source46b7c1ccc01eae9cf41292dde89ab32411ed5f79:
8 native PASS/1 FAIL before model use, because a loopback gateway was treated as an
unowned host application. All owned sandbox/template/local/remote artifacts absent.
Original result retained with SHA binding to the private receipt.

Eight actual original controller branches: before8 FAIL/40 PASS. Final relevant
suite130 PASS plus6 subtests,5.87s. Explicit created-ID/exact-resolved-URL binding
allows the owned local gateway, while missing/wrong binding, wrong proxy ID or
missing real-use ownership still rejects before any model mutation. Nonlocal
behavior preserved. Operator marker environment cannot be inherited; driver
rejects invalid/mismatching owned identity. Generator --check confirms all8 copies.

Spec39 PASS, all-template checker PASS/no claimed failures,224-document links PASS.
Runtime commands, Dockerfiles and manifests unchanged. Verification-file source
identities still change: fresh complete native/public-method/model/business/
CLI/full SDK/direct HTTP and independent cleanup on both providers are required
for all8 affected templates. Secret/diff/final-head CI and Registry gates pending.
No new provider qualification or full50 completion claim from these fixtures.
