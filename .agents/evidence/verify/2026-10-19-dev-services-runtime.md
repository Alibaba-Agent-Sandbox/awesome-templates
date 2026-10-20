# Verification: Development databases

Result: PARTIAL.5 actual-process tests PASS on non-root Debian13 using actual official extracted Debian PostgreSQL17.11/client/libpq and Redis8.0.2/tools packages. Package hashes are checked by apt metadata, no host package installation performed. Native liblzf/jemalloc dependencies extracted locally. Actual SQL/Redis write/read, wrong-password controls, stop/restart persistence, actual synthetic model-key absence from database environments, owned process/listener absence, caller data preservation and unrelated-listener preservation verified.

Earlier local prerequisite attempt omitted two required Redis shared libraries; after extraction, a real CLI flag error (--host unsupported) was corrected to -h/-p. Real wrong-password control exposed redis-cli exit0 on protocol error; -e now makes that failure observable. Failed attempts were not passes. Full self-test/HTTP/spec/image/cloud checks remain pending. No provider badge or Issue closure.

PASS: actual full local HTTP L0,5 assertions, including SQL/Redis self-test and
independently deleted/absent nonce data through server files endpoints. Actual
self-test confirmed persisted DB/Redis values across real stop/restart.

Follow-up PASS:6 real-process regressions including self-test preservation of a
caller file and removal of all nonce-owned data. Full required-engine HTTP6
assertions PASS/0 SKIP. Strict24 source templates plus skeleton and121 links
PASS before integration. Shared Ubuntu contract checks may explicitly skip
unavailable/mismatched database pins; a required Debian13 non-root CI job runs
actual exact database packages, all tests and complete HTTP with REQUIRE=1.
Image smoke also requires both actual engines/readback. No backend gate weakened.
