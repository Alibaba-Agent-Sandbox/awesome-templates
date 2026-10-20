# Chrome visible CDP preparation verification

Status: PARTIAL. Date:2026-10-20. Scope: uncommitted initial Chrome1.0.0 source, shared steps/image port forwarding and exact archive transport. Refs https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/61.

Executed: `python -m pytest -q chrome/test_commands.py chrome/test_protocol.py`:18PASS0.36seconds. Authored fixtures exercise validation, secret isolation, exclusive PNG, process cleanup, real local RFB protocol and HTTP auth. No native browser installed or run on operator.

Source-only `_run_one(Path('chrome'), <controller-venv-bin>)`:7PASS/0FAIL,1native-GUI SKIP; controller exit0. This is not image/native desktop/provider acceptance.

BLOCKED until executed: strict/spec/docs/shared regressions, actual image build and SDK-created native Express steps/full HTTP CDP/RFB/VNC input/frame/artifact/independent owned cleanup. No provider qualification, model or benchmark claim. No cloud resource created by these local checks.

Additional executed checks: targeted native/shared regressions46PASS/1wire-test deselected29.62seconds (wire requires committed COPY); strict all-template conformance0violations; public Markdown174documents0link failures; both actual SDK Markdown snippets syntax PASS. Initial strict run found missing literal CLI/CLI-Issue references; corrected, no checker weakened. Image/cloud remain NOT RUN.
