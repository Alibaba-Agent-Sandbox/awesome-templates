# Chrome visible CDP preparation verification

Status: PARTIAL. Date:2026-10-20. Scope: uncommitted initial Chrome1.0.0 source, shared steps/image port forwarding and exact archive transport. Refs https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/61.

Executed: `python -m pytest -q chrome/test_commands.py chrome/test_protocol.py`:18PASS0.36seconds. Authored fixtures exercise validation, secret isolation, exclusive PNG, process cleanup, real local RFB protocol and HTTP auth. No native browser installed or run on operator.

Source-only `_run_one(Path('chrome'), <controller-venv-bin>)`:7PASS/0FAIL,1native-GUI SKIP; controller exit0. This is not image/native desktop/provider acceptance.

BLOCKED until executed: strict/spec/docs/shared regressions, actual image build and SDK-created native Express steps/full HTTP CDP/RFB/VNC input/frame/artifact/independent owned cleanup. No provider qualification, model or benchmark claim. No cloud resource created by these local checks.

Additional executed checks: targeted native/shared regressions46PASS/1wire-test deselected29.62seconds (wire requires committed COPY); strict all-template conformance0violations; public Markdown174documents0link failures; both actual SDK Markdown snippets syntax PASS. Initial strict run found missing literal CLI/CLI-Issue references; corrected, no checker weakened. Image/cloud remain NOT RUN.

Integrated main b749fa15d148c2cb410083221572c0a66f0671d4, preserving accepted Tau2/Droid guards, tests and records. All targeted native/shared tests51PASS36.39seconds including immutable COPY wire/exact archive controls; full specification57PASS13.153seconds; explicit new Markdown/record links5documents0failures. Added fail-closed native-GUI skip rejection to both cloud controllers; its targeted regression is rerun separately.

Final controller skip rejection regression7PASS0.84seconds; integrated strict all-template0violations. Cloud source freezes after this commit.

First actual source f786d60a538831a87822a86cdb653d81702f64eb: L1 run39508114980 actual image build PASS, image-user genuine smoke FAIL at ready/RuntimeError; source wheel/non-root checks PASS. Actual SDK-created canonical native steps reached official READY and creation, but both CLI and SDK chrome_smoke FAIL; full HTTP NOT RUN. Independent owned sandbox/template cleanup true and private OSS archive/bucket cleanup true. Original failing receipt retained in chrome/evidence. No native desktop pass inferred. Following1.0.1 diagnostics add fixed stage/error-code and bounded RGB-only observation; no raw URL/page/password/exception contents are exposed. Root cause not yet established.
