# Named resource contract: CI follow-up

Scope: follow-up to the [named resource decision](../../notes/proposed/architecture/2026-11-13-named-resource-contract.md), Issue 309 and PR 311. Baseline: `6009ae6`.

## Failure evidence and decisions

GitHub Actions run [43409623256](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/43409623256) failed in local-e2e job 131832488256 and media-tools-offline job 131832488416. Public job logs were downloaded and inspected independently.

- SWE still read `sandbox.instance.envs`. Its test now reads the Dockerfile-derived image environment through the existing engineering projection. The required tool-call protocol, 30-step / 600-second budget and cleanup assertions remain intact.
- Continuing the subsequent CI groups exposed agents-cli's canonical HTTP fixture still reading `sandbox.start`. It now uses the engineering projection's template-owned business startup. Both actual startup forms, closed endpoint policy and authenticated HTTP assertions remain tested.
- Independent review found no further raw retired manifest reads in template tests. It found two checker messages incorrectly directing authors to native snapshot commands; those now identify the business runtime declarations in `scripts/template-checks.json`. Validation behavior is unchanged.
- Media's CI server exited before readiness, with stderr suppressed by the existing fixture. The unmodified exact dependency suite passed twice locally, including Debian Python 3.13.5. No media production defect or cause was reproduced. Do not label this fixed, change its version pins, or weaken its assertions; a new remote run remains required.

## Passed verification

- SWE: 36 tests.
- Subsequent CI regression groups: OSWorld 47; agents-cli 53; agents-api 20; Express socket 3; Qwen 76; Codex 27. Together with SWE: 262 tests.
- Media: 59 tests on Python 3.13.13, then 59 on Debian Python 3.13.5, with published client/server 0.4.0a6, httpx 0.28.1, pytest 9.1.1 and actual FFmpeg `7.1.5-0+deb13u1`. The unmodified real local media E2E also passed authenticated HTTP, independent random-PCM artifact roundtrips and owned-file cleanup.
- `scripts/test_spec_tools.py`: 57 tests. `scripts/check_template.py --all`: no violations.

## Limits and unsuccessful checks

An initial attempt to combine distinct template pytest groups in one invocation failed collection because several test modules share filenames. Rerunning in the separate invocations used by CI resolved collection. OSWorld initially lacked lxml locally; installing CI's exact lxml 6.0.2 enabled its successful run.

The broader local runtime runner completed with 35 passed and 13 failed. This environment lacks several CI prerequisites, including Pillow and pypdf, and several installed native CLI versions do not match template pins. These failures are retained; this run is not a complete local E2E pass or a diagnosis of every failure. The owned runner process group is absent and its generated working directories were cleaned. No further toolchain installation or cloud/model testing was performed.

The refreshed remote CI and consumer CLI source pin are managed separately. Historical evidence remains unchanged. No public release, image build or provider qualification is claimed by these checks.

## Final executable dependency

The coordinated CLI source pin is now `dcc3dd265c38ebf179cb7ea063cac0a335232cc3`,
including installed-package entry verification and embedded native Devs workers for
the standalone binary. The previous refreshed owner run passed all seven E2E jobs
and all 47 image jobs plus their plan job. Updating this source-only CI dependency
does not change the canonical schema bytes committed at `6009ae6`.
