# Media template actual image and CI confirmation

Date: 2026-10-18
Result: PARTIAL

## Exact remote source

[PR 106](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/106), draft, exact runtime source `9b30d8af1a69b34ed25409ecd381ef211aa66464`, stacked on OCR PR 103. The initial implementation and failed attempts remain in [the original record](2026-10-18-media-tools-runtime.md); this new evidence preserves their history.

## Actual results

All six remote checks completed successfully on this source head:

- [Actual L1 image job](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/39088318312/job/117559491304): Docker build succeeds with exact installed FFmpeg pins, non-root image user, and three actual offline image commands: `media_version`, sample-exact FLAC `media_smoke`, and independently probed H.264 MP4 `media_video_smoke`. No key, image push or provider registration was required by that image job. L1 is PASS for this source.
- [Debian 13 native/SDK/HTTP job](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/39088318271/job/117559464900): 43 actual native/SDK regressions passed, zero skips, exit 0 (10.58 seconds); then 21 required-engine HTTP assertions passed, zero failures/skips. That includes actual MP4 H.264, codec dimensions, owned cleanup, external random PCM artifact roundtrip and independent every-sample equality. The independent push job also completed successfully.
- Both complete repository `local-e2e` jobs succeeded: [PR run](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/39088318271/job/117559464719), [push run](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/39088314906/job/117559455273). These are source L0, distinct from image/provider tiers. The image-selection plan also passed.

## Follow-up from actual failure

Default glibc allocator arenas under the 1 GiB virtual address-space cap caused libx264 startup failure in real Debian CI, while local native tests and FLAC passed. The actual generated-fixture native regression exposed encoder exit 187. Setting `MALLOC_ARENA_MAX=2` in the scrubbed child environment fixed the same native MP4 regression on both real CI jobs without increasing the 1 GiB address-space, CPU, file or time limits. The product still omits native media diagnostics; verbose diagnostics are confined to the explicitly generated test fixture. The new video smoke ensures image/provider checks cannot substitute a successful audio conversion for MP4 functionality.

Native group cleanup regressions retain their live-child assertion while accepting both Linux `FileNotFoundError` and `ProcessLookupError` when `/proc` disappears during a successful kill/readback race. No failed native process or living descendant is treated as a pass.

## Current limits and ownership

Canonical `scripts/express_e2e.py media-tools` through the actual CLI deployment path has NOT RUN. There is no provider receipt, no `tested_on` entry and no status promotion. The PR remains draft and Issue 58 remains open; no merge is claimed. L3 is N/A; L4 NOT RUN. This confirmation update changes records/document links only; runtime files remain identical to the above reviewed source.

All source-test servers and native groups were stopped/reaped; unique controller uploads and converted artifacts were removed. GitHub's actual image job retained its ordinary short-lived archive artifact under the inherited selected-image export policy. No cloud compute, official template, ACR repository, model turn or credential upload was created by these checks.
