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
