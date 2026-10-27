# Cookie-preserving IDE endpoint and authenticated workbench check

Result: PARTIAL (regression fixed; real-provider reruns pending)

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
