# OSWorld screen/viewport follow-up — 2026-10-16

Status: PARTIAL. Refs [Issue 36](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/36) and [draft PR 94](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/94).

## Actual image failure retained

Fixed browser-cache source 65ff095d3f8a02829c84ea0166958d6b09dd68d1: [L1 run 38861410243](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/38861410243), job 116844359241, FAIL. The real Docker build succeeded. Non-root/network-disabled smoke failed with `TimeoutError (browser-attachment)` after 12.5 seconds. This stage included CDP connection and a ten-second requirement that page inner dimensions equal the whole screen. The image log did not expose actual viewport dimensions, so this does not prove which operation timed out. The earlier browser-location defect is separately reproduced/fixed and its evidence remains historical.

Both complete remote local suites succeeded: [PR run 38861410294](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/38861410294) and [push run 38861405423](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/38861405423). They do not override failed L1.

## Correction and real acceptance gates

An Xvfb screen size does not imply an equal browser viewport. Keep the real 1024×768 PNG check, require a visible nonzero page, and separately stage viewport initialization. Read only numeric screen/outer/inner/content-offset geometry; reject malformed/private string or nonfinite measurements. Startup and task setup return this geometry. Smoke prints only numeric fields, uses actual DOM rectangles plus content offset, and still requires real native input, baseline zero, final upstream score one, changed pixels and independent complete Unicode destination readback. The external HTTP fixture uses its known page coordinates plus the returned actual offset. No CDP viewport resize, DOM write or skipped GUI gate earns acceptance.

## Executed checks

- PASS: 72 regressions: 43 OSWorld plus 29 existing selector cases, including unequal screen/viewport geometry and invalid/nonfinite diagnostics.
- PASS: strict checker across all 19 directories, spec regressions (22 cases plus 25 subtests), changed Python syntax, local documentation links and whitespace checks.
- PASS: native actual full smoke using official Playwright cache resolution, original HOME and installed Google Chrome 150.0.7871.114. Observed screen/outer/inner all 1024×768 with zero content offset. The full task and exact 4096-character Unicode DOM readback passed.
- PASS: canonical authenticated HTTP full required-GUI suite, 18 checks with the same cache/native environment, including external uploaded task, score 0→1, fresh upstream XML, independent PNG checks and cleanup.
- Diagnostic variant, not product acceptance: a private runtime copy replaced `--kiosk` with `--window-size=900,650`. Actual screen was 1024×768, outer 900×650, inner 892×503 and content offset (14,157). Startup, real click and paste succeeded, but the original Tab→Enter sequence failed at keyboard-submit; a read-only diagnostic observed the input remained focused after Tab. This FAIL is retained, and no claim is made that all window configurations pass. Product code continues to use kiosk. This variant downloads no browser and is not the pinned image.

The previous cache evidence and source fingerprints remain historical. The fixed image must be rebuilt and its actual geometry/GUI results checked. Changed-image Express SDK/HTTP/CLI, cleanup and the full benchmark remain unverified; tested_on stays empty and the original Issue remains open.

## Source fingerprints

- `osworld/commands.py`: SHA-256 `22f7814416e0dc52cb0c0b04deae8323467a785db6601d8b36603abcb396a78d`.
- `osworld/runtime.py`: SHA-256 `9037591a81cc47d86ad78b701eaa872175d5f74eeff457d07e9755aa2eb2323d`.
- `osworld/e2e_test.py`: SHA-256 `07a4fa0615a9329dff948d19c411c0e60e8b916465d725ea5aeff2f2ea3ab2d1`.
