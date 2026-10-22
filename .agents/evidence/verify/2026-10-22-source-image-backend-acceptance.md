# Source image backend acceptance — 2026-10-22

Result: PARTIAL

Base: da1da4193bb31c28cb252d745b2012fd1d011c4b. Scope: shared HTTP fixture
enforcement, existing Express image runner, optional native OpenSandbox workflow
and controller. No template runtime source has changed at this stage.

- `python -m pytest -q scripts/test_template_http_acceptance.py scripts/test_ci_image.py`:
  PASS36; actual subprocess tests reject false success after required operation
  skips, zero checks or failed assertions and verify operator-key isolation.
- A manual29-template missing-current-image-HTTP export was accepted by GitHub:
  [run39747846635](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/39747846635).
  Acceptance is not yet claimed; the full export/runtime batch is pending.
- Native OpenSandbox pilot/full46 and additional Express image runtimes: NOT_RUN
  at this checkpoint. Full completion and Issue185 closure remain blocked until
  actual per-template receipts pass; existing steps46/46 remain separate.
- No new cloud resource or private registry transfer has been created by these
  local regression checks. Generated test keys are not published. Historical
  merged evidence remains unchanged.

- `python scripts/test_spec_tools.py`: PASS57.
- `python scripts/check_template.py --all --strict`: PASS46 sources plus skeleton, zero claimed spec failures.
- Workflow YAML and both new controllers compile: PASS. New bilingual documentation/record link checks are run before publication.

## First original OpenSandbox pilot

Actual native run39749792427 failed on both python-hello and node-web at the
explicit-user UID probe; SDK/container/process cleanup passed for both.
The unchanged images already select USER user. The next pilot tests the actual
image-default identity and still requires a numeric UID greater than zero;
explicit same-user switching on the legacy execd is not qualified. Preserve
manifest environment defaults instead of replacing published non-secret
settings with empty values. See the dated initial-pilot-failures JSON.

## Second original OpenSandbox pilot

Run39750661983 observed UID1000 and complete actual native HTTP checks21
(python-hello) and60 (node-web); SDK/container/engine/server cleanup passed.
The overall run correctly remains FAIL because the controller queried unused
`opensandbox` client metadata; this fixture installs the original
`opensandbox-server` distribution. Fix the distribution lookup, retain both
failed receipts and rerun the native matrix. No runtime success is published
as an overall pass from this failed workflow.

Shared fixture/image/steps-controller regressions: PASS45.

## Express transfer and command-surface regressions

All29 missing-current-image-HTTP source images exported successfully in
run39747846635. First two transfers failed before native runtime: the task driver
had relocated all temporary directories to the object-backed workspace, which
cannot create the registry-auth fd symlink (actual errno22). Add an explicit
private archive root without moving RAM-only auth away from the native temporary
filesystem. Keep actual auth bytes in anonymous RAM. Deleted2,110,424,490bytes of
resolved first-transfer archives; retain small failure/ownership records.

The next two attempts uploaded verified private images but the existing harness
called removed `template create`. Actual published CLI0.4.1 and sourceCLI0.4.5
both expose `template from-image`. Both requests were rejected by the parser
before a registration callback; no known template/sandbox IDs and no sandbox
create attempt. Independent official exact-alias and SDK absence checks passed;
registry cleanup also passed. The original attempts remain FAIL. Correct the
canonical image route and receipt operation; preflight the actual CLI help before
archive/cloud operations. The existing image lifecycle regression failed before
that correction. A new local-protocol-helper regression also failed before adding
transitive dependency preflight.

Verified publisher assets independently match the actual local tools:
CLI0.4.1 SHA256766b0b10c3e4c633632dad503ae7750183a8be41974a9d048f060836f8cb0c44;
crane0.22.1 SHA2568e75c326adb43b053cfd78b9b987663f8f4fe4557f4d3915905643f25c730992.
Express controller SDK source:34e7e011c5569f77b7f605e65313be7498f6cf02.

## Native source matrix and Chrome controller dependency failure

Native run39751400293 produced real individual source API/HTTP and independent
cleanup passes; its full matrix is still in progress. Chrome's real native image
and shell/named smoke passed, but external HTTP failed8PASS/1FAIL because the
controller's local CDP/RFB helpers need aiohttp and Crypto. Keep this as FAIL and
add the existing complete hash-locked chrome/requirements.lock to the native
controller environment. The local transitive-helper preflight failed before
correction and passes afterward; no template source or native runtime gate was
weakened. Native cleanup passed for the failed Chrome attempt.
