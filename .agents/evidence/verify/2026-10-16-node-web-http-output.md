# Node Web HTTP result protocol correction

Result: PARTIAL

Refs [Issue29](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/29),
[focused reproduction](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/29#issuecomment-6210886875).
Independent branch based on a361f490555ead0ff67081ffb4874abf292a1b2f;
commands.py/Dockerfile/template.yaml/index.js are unchanged.

## Baseline and local verification

- Confirmed original node-web/e2e_test.py SHA256
  271ae3ca8008f09da4bf25bb8d2b50d9d323b87242906e2f091c021728c02617,
  matching the previous rejected actual-image report. __main__ calls main.
- FAIL, intentionally preserved red baseline: new real HTTP/Node/npm regression
  against the unchanged script. Local runner returned pass/exit0; strict regex
  observed PASS0/FAIL0/SKIP0, so the regression failed in4.03s. This is an output
  protocol mismatch, not evidence that the script did not execute.
- PASS after narrow formatter fix: `python -m pytest --import-mode=importlib -q
  node-web/test_http_output.py`,2 tests in4.79s. Complete real SDK HTTP server and
  real Node/npm service/build suite yielded60 recognized PASS,0FAIL,0SKIP. Separate
  real HTTP503 fixture yielded nonzero and one bracketed FAIL; it is a synthetic
  unhealthy service control, not a provider/product failure.
- Environment: Python3.11.15, agent-sandbox-server0.3.0, httpx0.28.1,
  actual Node22.22.2/npm12.0.2 already installed. No new package install; original
  HOME retained, npm configuration/cache redirected through official npm_config
  variables to an owned temporary directory, then removed.
- PASS: checker node-web conformant; git diff --check.
- PASS:24 relative Markdown links and2 bilingual Python examples parse/resolve.
- Static inspection of all17 current product template e2e formatters (including
  indirect record(line) helpers) found only node-web unbracketed. No broad parser
  relaxation is introduced. The initial host Python metadata probe lacked the
  server package; the actual regression/confirmed versions use the existing
  paired SDK test virtualenv, with no change to either environment.

## Image and delivery gates

New actual-image HTTP acceptance pending. The prior root batch result remains
FAIL/refused (exit0 with0 recognized checks), unchanged. Do not retroactively call
that rejected result an accepted pass. A matching existing image may be borrowed
read-only from the batch owner, with separate owned template/sandbox resources;
borrowed registry resources must not be deleted by this task.

Normal remote CI/draft PR pending. Canonical abx template deploy and formal
provider metadata/Issue29 completion are separate gates; tested_on remains empty.
