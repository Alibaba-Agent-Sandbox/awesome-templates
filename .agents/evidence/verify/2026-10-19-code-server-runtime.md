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

## 2026-10-20 browser review continuation

Reconstructed the reviewed browser controller after ephemeral environment reset.
Earlier temporary outputs that were not published are not treated as durable
acceptance. Exact Playwright1.58.0/Chromium1208 and official code-server4.141.0
are installed for genuine local browser/PTY/editor regressions. TLS remains on,
private NSS imports only roots already trusted by the operator's SSL context,
cloud/model keys are not forwarded to browser children, and cleanup uncertainty
fails. Current source local tests and genuine cloud rerun require new records.

PASS:14 actual local lifecycle/browser/environment tests, including real browser
workbench JavaScript, PTY terminal nonce write, editor save and independent local
file bytes/cleanup. PASS: dedicated4-test browser suite after adding browser
teardown-failure injection; the actual IDE is still stopped and its state removed.
Only that cleanup-control negative mocks the browser; full UI runs real Chromium
1208. Exact code-server4.141.0 installed bytes718143901 from verified official
asset.117 document links PASS. Source/runtime image contract remains1.0.0: the
new controller is external acceptance tooling. Actual current-controller cloud
UI and current-head CI/merge remain pending. No historical temporary run is
converted to a passing provider receipt.

## Genuine current image result and default-domain control

FAIL: actual image-backed Express attempt completed CLI/runtime work and full
HTTP5 PASS/0 SKIP, but Chromium navigation raised Download-is-starting before
workbench load. No canonical provider pass was published. Owned sandbox/template
absence and private registry cleanup independently PASS, image digest readback
after runtime matches. Failure receipts retain their exact controller hash.

PASS negative control: a new owned base sandbox served fixed HTML from stdlib;
external HTTP200/text-html/body matched, default-domain forced attachment was
observed, real Chromium downloaded with TLS on/private already-trusted CA roots,
and owned sandbox list plus separate SDK get_info_by_id confirmed absence. The
first control used an unavailable optional GET method (fieldfalse, list absence
confirmed); a distinct corrected run verified both. Actual control files remain
unchanged. Official FC web-functions documentation confirms the custom-domain
requirement; no account domain/security configuration was changed.

The external controller now gives a specific PreviewDomainError before browser
startup and still stops its owned IDE. Focused mock-HTTP attachment/cleanup
regression PASS; this controller-control test is not cloud/UI acceptance. Full
real browser/PTY/editor4-test suite passed before adding the diagnostic. Latest
CI must exercise the complete updated local suite; custom-domain cloud UI remains
BLOCKED pending a usable mapped domain. Keep Issue53/PR127 uncompleted.
