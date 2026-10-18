# OSWorld image browser-path follow-up — 2026-10-16

Status: PARTIAL. Refs [Issue 36](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/36) and [draft PR 94](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/94).

## Actual first image result

Source head 5bae8777fdc5c572bcce16a31cce7c07847ed26c: [L1 run 38859920017](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/38859920017), job 116839689806, FAIL. The standalone Docker build succeeded. The real non-root, network-disabled image smoke failed during desktop initialization, before any image acceptance was earned. Build log artifact 12028443181 is 21947 bytes; it is a log, not a successful image archive.

Both complete local CI runs actually succeeded: [PR run 38859919939](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/38859919939) and [push run 38859857429](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/38859857429). These do not override the L1 failure.

## Defect and change

The Dockerfile installs Chromium in PLAYWRIGHT_BROWSERS_PATH=/opt/osworld-browser. The worker's environment allowlist omitted that nonsecret setting, so official Playwright resolved its default HOME cache instead. Native source checks had explicitly selected the installed host Chrome with OSWORLD_BROWSER, masking this integration defect.

Pass through PLAYWRIGHT_BROWSERS_PATH without copying credentials or changing HOME. Extend the real fixture-worker environment regression to require that exact configured cache. Initialization failures now report only an internal fixed stage and exception class; submitted paths, text, URLs and native stderr remain omitted. A regression verifies that a private path cannot enter that diagnostic.

## Executed checks

- PASS reproduction: baseline parent commands from 5bae877 with the current diagnostic worker, original HOME and no OSWORLD_BROWSER override failed specifically at `browser-location` when its configured cache was dropped.
- Native resolution fixture: use actual official Playwright's executable-path calculation in a temporary cache, pointing its expected executable at the already installed Google Chrome 150.0.7871.114. This reuses a real browser and downloads no browser. It proves environment/path integration, not the image's pinned Chromium version.
- PASS: `python -m pytest -q osworld/test_commands.py osworld/test_tasks.py osworld/test_http.py scripts/test_select_image_templates.py`: 71 cases (42 OSWorld plus 29 selector), after the fix.
- PASS: native full desktop smoke through the official cache resolution path without OSWORLD_BROWSER, including actual upstream evaluation 0→1 and exact 4096-character Unicode DOM readback.
- PASS: canonical authenticated HTTP with the same cache resolution setup: all 18 checks, including external uploaded task setup, baseline zero, real GUI input, independent PNG/DOM observations, final upstream score one and owned cleanup.
- PASS: spec regressions: 22 cases plus 25 subtests. Strict checker across all 19 directories, changed Python syntax, local documentation links and whitespace checks passed.
- Pending: a new actual L1 run on the fixed source.

The initial [native evidence](2026-10-16-osworld-browser-slice.md) remains historical; its source hashes and prior checks are not overwritten.

## Actual detached-process audit

On the original 5bae877 source and native Google Chrome 150.0.7871.114, normal stop after the full desktop smoke, request timeout, and abrupt worker SIGKILL each started 12 Chrome-related processes, including 2 genuine crashpad handlers with PPID 1 and separate PGID/session. Their unique private-state path in argv plus PID/starttime fingerprints proved task ownership; full argv/private paths were omitted from records.

After cleanup each complete Chrome/crashpad process list was empty, including the detached handlers; owned live survivors were zero. This audit goes beyond checking the original PGID. No extra crash-handler flag or widened signal range was added. The handlers exited when owned Chrome clients stopped. Deliberate setsid escape remains outside the generic group boundary; actual pinned-image and provider lifecycle cleanup still require separate verification.

## Remaining acceptance

Actual fixed-head L1, successful image archive, changed-image Express SDK/HTTP/CLI acceptance and owned provider cleanup remain pending. Full OSWorld VM/Office/benchmark/model coverage is outside this slice and the original Issue remains open. Status is experimental and tested_on is empty.

## Follow-up source fingerprints

- `osworld/commands.py`: SHA-256 `76b8346f0fecb639f899a0e79b168689abacef834566e5359960dde74952d383`.
- `osworld/runtime.py`: SHA-256 `e6508426fafdc49836949f0a0d53d67dd2ec67cc1f20a2c25c2d1a5f7f62207a`.
- `osworld/e2e_test.py`: SHA-256 `cf56d904ada180b4da9f32830e29e6491c4be18a9142b4713aefcb44be6682ab`.
