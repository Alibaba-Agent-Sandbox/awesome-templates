# Verification: polyglot toolchain

Result: PARTIAL. Exact official Go1.25.14, Rust1.90.0 and Temurin21.0.12.1+1 hashes obtained from upstream manifests/release checksum assets. Runtime source, installer and both architecture assets added. Local/source, actual image/cloud checks and merge are pending; no compiler/provider pass is claimed here.

PASS: four real-process regressions (output, nonzero, redirected descendants and
deadline). Strict target conformance and Markdown links117 documents/0 failures.
Actual HTTP L0 PASS with explicit compiler smoke SKIP because the local host does
not have the exact distributions. Initial local harness used system Python and
failed its server import; corrected PATH to the paired test venv, then reran.
Generated native steps serialize to11548bytes, below the conservative15KB limit;
this preflight is not cloud acceptance. Actual L1/Express remain pending.

Container filesystem review corrected the budget measurement: df/statvfs on a
Docker overlay reports its host backing usage. The installer now uses du -sx
--block-size=1 / to enforce8GiB on the actual visible image rootfs. The true
Express runtime still reports rootfs used/free through statvfs. This is a
measurement correction, not permission to exceed the same image budget.

CI selector follow-up: preserve the frozen23-template canonical source approval
boundary while permitting new independently verified catalog entries. The
authorization regression rejects every unreviewed added name; no credentials
or cloud workflow authorization are broadened.13 real authorization tests PASS.
