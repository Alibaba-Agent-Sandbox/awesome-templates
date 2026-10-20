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

## 2026-10-20 source review

FAIL before correction: native child inherited synthetic cloud/model/server
credentials and injected compiler/loader options. A real child-process regression
precedes the fix; only synthetic selected variables are inspected. The runner now
filters environment and drains both streams concurrently with a256KiB per-stream
cap, preserving90-second deadline and unreaped owned group cleanup. Source also
explicitly assigns workspace ownership (shared missing-ownership inference, not
a claim of an observed polyglot provider write failure). Contract bumped1.0.1.
Old1.0.0 exports and FAIL attempts do not qualify this profile. Stopped obsolete
artifact download before registry intent creation, confirmed absence and removed
only the partial owned archive. New actual image/full Express checks required.

Corrected focused verification:6 actual process regressions PASS, including
noisy native process output bound, actual synthetic-credential/loader exclusion,
normal/nonzero descendant cleanup and timeout. The credential regression also
fails against preserved original HEAD source, without printing real environment
values. Strict target conformance and117 document links PASS. Current-head image
and genuine1.0.1 provider acceptance remain pending.

Integration preserved main's apply-patch checks, Kimi source row and separate
managed-template namespace while retaining the compiler installation/test rows.
Legacy statvfs response field names remain compatible; both READMEs explicitly
distinguish visible filesystem capacity from actual du-based image-size budget.
The new1.0.1 archive can be reused only when all image/runtime inputs match the
export's exact public Git revision. Current-head CI remains required.
