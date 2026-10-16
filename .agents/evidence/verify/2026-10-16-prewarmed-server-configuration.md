# Verification: prewarmed command-server configuration documentation

- Date: 2026-10-16
- Result: PASS for documentation checks; no new cloud execution is attributed to this documentation patch.
- Source base: Pi a361f490555ead0ff67081ffb4874abf292a1b2f.
- Issue: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/93
- Runtime evidence owner: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/88

## Verified facts reused

The original Aider image attempt supplied the documented three settings through Sandbox.create envs. Its default setup did not satisfy all three required flags, so the required model run failed before making a model call. That record did not store each flag individually; this patch does not claim all three were false.

A second independent attempt used the exact reviewed image and unchanged commands, explicitly starting a new port-9010 server through the native process API with selected env settings. SDK, HTTP and CLI each asserted all three setup flags true. The model suite completed 21 PASS, zero FAIL and zero SKIP: read-only ask, selected source fix, new report and exact artifact, preserved original tests, independent target tests and six held-out calculations. All ten cleanup flags passed, including sandbox inventory, official template inventory and registry tag/repository 404 readbacks. These facts support the process-start explanation, not a general guarantee about every provider's create environment.

The complete Qwen code example is an API illustration with documented Qwen configuration names; this documentation patch did not run an additional Qwen model session. The guide explicitly states that distinction.

## Documentation checks

- `python scripts/check_template.py --all --strict`: all 18 directories conformant, zero failure.
- `python scripts/test_spec_tools.py`: 22 tests plus the existing checker subcases passed in 8.517 seconds; only synthetic harness fixtures, not a cloud run.
- Independent source review corrected token-aware calls to `ServerClient.commands.run`, and the `/health` server-auth exemption was checked against the actual endpoint/router source. These corrections also update the affected existing Qwen, Node web and Python hello instructions.
- Changed-document local-link check: 316 local targets exist across 46 scoped Markdown files.
- Python fenced examples: all 45 compile; documentation syntax checking does not execute cloud snippets.
- Product-file scope and `git diff --check`: PASS, Markdown-only changes. Configured-secret staged scan is performed before commit.
- Independent peer review found two documentation mistakes during preparation: a missing `.commands` API namespace and an incorrect health-auth statement. Both were corrected before publication; actual SDK/server source confirms the final wording.

## Boundaries

No template command, Dockerfile, YAML, catalog qualification or provider-pass JSON changes. Formal canonical deployment remains pending in the separate review. No model or cloud credential, endpoint value, sandbox/template ID, signed URL or raw provider output appears in these documents.
