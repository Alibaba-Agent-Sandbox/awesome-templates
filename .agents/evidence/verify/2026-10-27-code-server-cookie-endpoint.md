# Cookie-preserving IDE endpoint and authenticated workbench check

Result: PARTIAL (both provider workflows PASS; Registry/public delivery pending)

Date2026-10-27. Original source46b7c1ccc01eae9cf41292dde89ab32411ed5f79 on
OpenSandbox1.1.1 default internal server proxy: native5 PASS, actual documented
browser workflow FAIL after its first CLI check. Original inspected screenshot
shows real workbench connection timeout. All owned sandbox/template/local/remote
artifacts independently absent. Original failed receipt preserved.

Official installed server1.1.1 api/proxy.py SENSITIVE_HEADERS includes Cookie and
is used for HTTP/WebSocket forwarding. The fixture reproduces the lightweight
false positive: login document mentions workbench, original controller passes.
Regression before fix:1 FAIL/1 PASS; after fix:2 PASS. Wrong target cannot pass by
returning a login page; owned lifecycle cleanup confirmed on both fixture paths.

Broader local command tests:11 PASS/2 FAIL because the platform host supplies
code-server4.127.0 rather than required4.141.0. No global platform binary is changed.
Current CI installs the exact upstream4.141.0 asset; actual provider runs also must
use it. These local package-required failures are not counted as passes.

Spec PASS39, all-template checker PASS, documentation links PASS224 with zero
failures. Secret/diff, current-head CI and fresh full
Express/direct OpenSandbox native/public-method/CLI/full SDK/HTTP/browser editor
runs and independent cleanup are required before delivery. No provider pass yet.

## Fresh complete real-provider execution

Actual published CLI0.5.7/client-server0.4.0a6, source4c4d1a700b76135333d8a85f32008f59745cc926
(immutable combined verification branch; template folder tree exactly matches this
individual PR). Both Express and OpenSandbox complete native/public methods,
wrong-token, process/file round trips and fresh literal CLI/unchanged full README
SDK/direct HTTP business use PASS, with zero native failures/skips/not-run.
See per-provider complete JSON and method-audit.json in the adjacent evidence folder.
All owned sandbox/prepared/local/remote image artifacts independently absent,
zero retained/uncertain/cleanup failures. Registry qualification and publication
remain separate; original failures above are preserved.

Each provider:5 grouped native assertions and10 documented checks PASS. Real browser
password login, editor keyboard focus, edit/save, independent source execution,
source-file absence and original relay listener absence all passed. OpenSandbox
explicitly uses direct endpoint mode (plugin defaultfalse), preserving native
password/cookie authentication; server-proxy mode is not claimed supported.

Additional host diagnostic: exact4.141.0 upstream asset was installed in task-owned
FUSE storage without replacing platform4.127.0. Two full18-test host runs each
14 PASS/4 FAIL with native startup error timed out. Isolated pinned-version call
passes. These host failures remain FAIL; CI installs native4.141.0 and passes,
and the two actual provider image/browser workflows above independently pass.
No deadline, auth or editor-output assertion was relaxed.
