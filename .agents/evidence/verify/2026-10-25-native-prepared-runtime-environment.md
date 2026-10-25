# Native prepared runtime environment verification

Date: 2026-10-25
Result: PARTIAL
Issue: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/227

The scoped change is three maintenance source files and two existing test modules based on public commit 389302f5dc9429a4b215801dbd4025d4dba95f7e. No original running matrix source, business Dockerfile, command or manifest version was changed.

## Local regression

Using the existing verification environment with public client/server 0.4.0a6:

```bash
python -m pytest -q scripts/test_prepare_steps.py scripts/test_steps_http.py scripts/test_ci_image.py scripts/test_ci_image_archive.py
```

PASS: 72 tests. Running the new targeted tests against the original source produced 2 FAIL / 1 PASS: explicit runtime ENV was missing, and the prepared-reference helper did not accept the mapping. The build-only environment exclusion control already passed. This is local adapter verification, not a new provider matrix.

The regressions preserve explicit Dockerfile ENV expansion, original manifest values including empty secret declarations, exclusion of transient UV/cache environment, forwarding to the one existing launch consumer and unchanged image-consumer calls. This adapter's image-style defaults do not claim that the separate production native-steps wrapper has the same collision priority.

## Controlled same-instance diagnostic

The [sanitized diagnostic](2026-10-25-agents-native-env-controlled-diagnostic.json) used official CLI 0.5.5, SDK 0.4.0a6 and unchanged public source 389302f5dc9429a4b215801dbd4025d4dba95f7e. It ran separately from the frozen 46-case batch. Before retry, one owned application server had the expected token but lacked /opt/node/current/bin; HTTP reported RuntimeError, codex is missing. Runtime commands bytes matched the original source. The installed binary was present outside the inherited PATH.

The diagnostic stopped only that uniquely owned application PID and confirmed its port closed, then started the same original command in the same sandbox with the materialized explicit Docker environment and original application token. HTTP returned codex 0.162.1 and qwen-code 0.23.0. The generic SDK execution environment on that already-created sandbox remained unchanged; the retry proves the application-process cause, not full new-manifest acceptance.

The original diagnostic attempt deliberately remained FAIL. Independent sandbox absence and per-owned-template typed E2001/readback cleanup both completed; unresolved_owned_cleanup was false. No candidate CLI patch was invoked and no credentials, endpoints or native identifiers are included.

## Remaining gates

Latest-head repository CI, independent review and the fresh full public-input matrix are pending. The original frozen native batch continues with its original source and retains each failed case; this diagnostic does not turn those failures into passes. The default Express Docker-to-ACR source path remains BLOCKED and is distinct from the native-step supplemental path.
