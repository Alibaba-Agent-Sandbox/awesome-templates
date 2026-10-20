# Verification: Goose terminal runtime

Result: PARTIAL. Official release1.54.0/sourcecd643d21 verified. Real GNU x64
archive80909320 bytes SHA256bf01cb6359f7a2b1acb54ca4827e1d059b18aabb3d2b75202e21066cfd3a3396
produced unchanged307756800-byte executable; actual --version returns1.54.0.
Official --help/source confirm stdin -, no-session/profile, provider/model,
max-turns and developer builtin. OPENAI_BASE_URL is a supported exact upstream
setting; no guessed host/path rewriting is used. License retained.

PASS:9 actual native/protocol/process regressions. Real local synthetic HTTP
fixture observes /v1/chat/completions, literal stdin, no advertised tools in
default chat and exact edit/read_image/shell/tree/write tools on explicit opt-in.
An initial test incorrectly expected an editor-named tool; actual pinned CLI
exposes edit/write, confirmed by the real request and reflected in the strict
assertion. This is not model/cloud evidence. Caller HOME unchanged, missing key
refuses before process, cloud/server/loader vars filtered, path/type guards,
nonzero/success descendant cleanup, output bound and deadline PASS.

Image, Express steps/image, real model, full remote API/current-head CI and merge
remain pending. tested_on stays empty; catalog experimental.

PASS: complete local HTTP9 assertions plus one explicit L3/model SKIP, with the
actual pinned native CLI; no provider/model claim. A first local invocation
selected host python3 without the SDK because the explicit venv interpreter did
not activate PATH; rerunning with the same venv on PATH passed. The native runner
is embedded in the standalone commands module to avoid a caller import-path
dependency. Whole image du budget now runs after SDK/runtime files, before USER.
All bundled license/notice/copyright members are retained when present. Strict26
catalog templates plus skeleton and129 documents PASS before publication.

Publication checkpoint:38 specification/controller tests PASS, strict26 catalog
templates plus skeleton PASS,129 document links PASS and all changed Python
modules compile. Source HTTP used the same activated venv as the SDK. No runtime
provider/model receipt exists yet; image and genuine step/model runs follow the
exact published source. CI receives no cloud/model credentials.

## Actual cloud attempts and controller correction

FAIL: actual step build reached official error in the native asset installer: combined byte/deadline budget protection fired. The response does not distinguish which branch. Known template deletion and independent absence were confirmed; no sandbox/model run or READY is claimed. See the new template-local step attempt and sanitized diagnosis.

FAIL: actual verified-image registration and primary CLI/SDK version smoke succeeded, but the strict-model helper replaced PATH without /opt/goose, so its secondary server could not find the installed CLI. The helper now preserves that directory. Review also found the copied controller expected a string, while the documented native Goose command returns stdout/stderr/exit_code. A real controller-flow synthetic response regression first failed for correct structured success and wrongly accepted a legacy string. The corrected controller requires typed stdout/stderr and exact integer exit0, rejects nonzero/boolean/string results, and retains all independent file/original-test/held-out gates. Four focused regression cases PASS. Runtime/Docker/manifest/assets are unchanged; only a separately recorded controller rerun on the same verified image can establish model acceptance. All owned sandbox/template/registry cleanup for the failed image attempt was independently confirmed. Historical failure receipts remain immutable.
