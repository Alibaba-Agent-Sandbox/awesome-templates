# Template usage simplification verification

Result: PARTIAL

Scope: files in the `fix/template-usage-simplification` branch for awesome-templates; no historical evidence or template runtime inputs were rewritten. Environment: Python 3.13, Node 22; credentials were not printed or stored.

PASS: 13 public launch runner unit tests; 58 specification tools tests; all template checks (zero claimed spec failures); 222 Markdown documents with zero link failures; both changed workflow YAML files parsed; Python compile check. Public npm CLI 0.4.14 and PyPI client/server 0.3.1a2 metadata fetched successfully. NOT RUN: the new 46×2 backend matrix, real-model tasks, full existing HTTP controllers. New runner/CI does not itself constitute backend acceptance.

No cloud resources were created by these local checks. Workflow execution and its resource cleanup are recorded separately. Refs https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/203 .

Adversarial review caught a wrong ServerClient close method before any cloud execution. Corrected to `aclose()` after all owned resource cleanup; regression proves a close failure cannot skip sandbox/template/image cleanup. Deletion uses independent control-plane GET with bounded eventual-absence polling, never connect/resume.

Third review used an actual Express journal shape: shared repository `python-hello`, unique per-launch tag. Artifact cleanup now verifies configured namespace and the exact journal tag prefix, then deletes only that tag and confirms absence. Regressions cover shared repositories and reject a foreign tag even when its repository contains the launch alias.

Matrix scheduling permits four independent runners at once (same 46×2 total tasks). Workflow YAML parsed successfully after this scheduling-only change. Diagnostics without `expect` are explicitly scoped to call-path success in both guide languages.
