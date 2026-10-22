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
