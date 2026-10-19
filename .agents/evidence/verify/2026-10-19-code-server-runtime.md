# Verification: standalone code-server

Result: PARTIAL. Official4.141.0 x64 archive239926515bytes verified against65bcd20b524d03eb1b5adb7f360244599ef0e5b74089a46a982d32c074b97a29. Real local password failure, correct login cookie and authenticated workbench HTML passed. The version inspector initially parsed a timestamp log line; it now extracts an actual semver output line, with pin assertion unchanged.

Local full HTTP acceptance passed5 assertions before cleanup readback was tightened. New lifecycle tests initially failed raw TCP connection/rebind assertions. A real empty-port negative control showed connect_ex returns0 through the operator network proxy, HTTP returns RemoteDisconnected, and the kernel has zero listening sockets. Earlier inference that a connected socket proved a surviving IDE was incorrect; it is not retained as a proven upstream defect. Cleanup now checks actual pidfd exits and kernel TCP listeners; tests are being rerun. SO_REUSEADDR accounts for kernel TIME_WAIT while still rejecting live unrelated listeners.

Visible image-rootfs budget uses du rather than Docker host statvfs. Native process credentials are filtered and caller config/state are isolated. Actual image/Express/forwarded UI, WebSocket/terminal and latest-head CI/merge remain unrun/pending. No provider acceptance is claimed.

## Corrected complete local verification

PASS:11 actual/negative lifecycle tests in3.94seconds, including actual
version/authenticated workbench, private config/mode and caller preservation,
credential-env exclusion, unrelated-listener protection, readiness deadline and
retained authority on cleanup error. Kernel TCP table positive/negative controls
replace the disproven raw-connect assumption; pidfds verify owned worker exits.
PASS: full actual HTTP L0 after the correction,5 assertions including a separately
forwarded local8443 authentication/workbench document and cross-request state.
PASS: strict target conformance; Markdown links117 documents/0 failures.
Image/Express/hosted current-head CI and merge remain pending.

CI selector follow-up: preserve the frozen23-template canonical source approval
boundary while permitting new independently verified catalog entries. The
authorization regression rejects every unreviewed added name; no credentials
or cloud workflow authorization are broadened.13 real authorization tests PASS.
