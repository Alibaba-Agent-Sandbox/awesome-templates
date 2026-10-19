# Verification: polyglot toolchain

Result: PARTIAL. Exact official Go1.25.14, Rust1.90.0 and Temurin21.0.12.1+1 hashes obtained from upstream manifests/release checksum assets. Runtime source, installer and both architecture assets added. Local/source, actual image/cloud checks and merge are pending; no compiler/provider pass is claimed here.

PASS: four real-process regressions (output, nonzero, redirected descendants and
deadline). Strict target conformance and Markdown links117 documents/0 failures.
Actual HTTP L0 PASS with explicit compiler smoke SKIP because the local host does
not have the exact distributions. Initial local harness used system Python and
failed its server import; corrected PATH to the paired test venv, then reran.
Generated native steps serialize to11548bytes, below the conservative15KB limit;
this preflight is not cloud acceptance. Actual L1/Express remain pending.
