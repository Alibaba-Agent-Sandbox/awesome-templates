# Pandoc template actual image and native CI confirmation

Date: 2026-10-18
Result: PARTIAL

## Exact source and actual passes

[Draft PR 107](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/107), runtime source `cf55b9f3f1b4a53d1f06a14fff93e74e9b138ae0`, independent of media-tools PR 106 and stacked on OCR PR 103. The [original verification](2026-10-18-document-tools-runtime.md) preserves local preparation and the actual initial remote failures.

- [Actual L1 image job](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/39089075796/job/117561750152) completed successfully: actual pinned Debian engine/data installation, non-root image user, exact `document_version`, and actual `document_smoke` DOCX/TXT generation, independent internal XML/text checks and owned cleanup. The image was built, not inferred from extracted packages. L1 is PASS for this runtime source.
- [Actual Debian native/SDK/HTTP job](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/39089075722/job/117561716104) completed successfully: **43 passed, zero skips**, exit 0 (3.20 seconds), followed by **20 required-engine HTTP assertions passed**, zero failures/skips. The matching [push native job](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/39089072760/job/117561707297) also succeeded.
- Image-selection plan succeeded. At this point the two whole-repository local-e2e jobs were still running; their result is not claimed from native/image passes. A follow-up latest-head inspection remains required.

## Actual failed startup and bounded fix

At initial source `7abe1c509f7f15607eb7994e89abeeddcb978a09`, installation-time `pandoc --version` succeeded but the same executable under native resource caps failed in the image and both dedicated Debian jobs; one inspected job reported 19 failed/23 passed. These failures remain historical evidence, not passed native checks.

The follow-up explicitly caps the inherited native stack at **8 MiB**, keeping the existing **1 GiB virtual address-space**, **256 MiB Haskell heap**, two runtime capabilities, two glibc allocator arenas, CPU/file/wall limits unchanged. A separate controlled actual-native reproduction sets the inherited stack to 256 MiB: the previous helper without a stack cap exits 1 with Pandoc's diagnostic that virtual memory is too low and at least 2304 MiB is needed; the same program/caps with the 8 MiB stack bound exits 0. The fix bounds thread stack reservation instead of enlarging the memory budget.

The version-only regression now covers both ordinary 8 MiB and deliberately large 256 MiB inherited stack settings. Both cases executed successfully locally (`2 passed, 41 deselected`, exit 0). This is an actual process/resource regression, not a mock, and requires no private document or credential. These additional test inputs do not change the runtime source accepted by the image job above.

## Review and remaining acceptance

Independent review found no material AST/writer/path/process correctness defect and separately executed actual native/typed-SDK tests plus DOCX list/table/safe-hyperlink/Unicode/content/hash/input-preservation checks. The noted operator-version ambiguity was resolved: every conversion checks the actual executable pin within its shared deadline, and a real wrong-version executable is refused before publication. Missing-source smoke failure still removes the previously published owned output.

Canonical `scripts/express_e2e.py document-tools` through actual CLI deployment, external CLI plus SDK smoke and strict official cleanup has NOT RUN. No provider pass JSON, tested_on value, official status or merge is claimed. Issue 55 remains open: HTML input, images, PDF, slides and LibreOffice are still NOT IMPLEMENTED. L3 is N/A; L4 NOT RUN. Required latest-head CI/review still applies to the final follow-up commit; old green checks are not relabeled as new-head checks.

Unique local test jobs/uploads/artifacts and native groups were cleaned. The normal image workflow retained its short-lived archive artifact under the inherited selected-image export policy. No cloud compute, official template, ACR repository, model call or credential upload was created by these checks.

## Exact-head whole-repository failure and input-order correction

At follow-up source `e7d8a1d3d160121f198005ffd0f7ec445cd33eed`, actual L1 and both dedicated native/SDK jobs passed, including 44 tests. Both whole-repository local-e2e jobs instead failed with **19 passed / 1 failed**, solely `document-tools`: [PR job](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/39089328338/job/117562478022), [push job](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/39089325663/job/117562469453). Their upstream installation/lint/regression steps had succeeded. The failure was the existing outside-workspace/network input HTTP assertion, not a network install hypothesis or provider failure.

The per-operation executable pin check ran before the bounded path snapshot; on the generic host without fixed Pandoc, a rejected path therefore raised RuntimeError for the missing engine instead of the established ValueError. Three new direct regressions with a genuinely unavailable executable reproduced the defect (3 failed before the fix). The correction validates path/bytes/UTF-8 first, then checks the actual executable pin before parsing, retaining one shared deadline and per-conversion pin enforcement. The HTTP assertion is unchanged and no acceptance case is weakened or removed.

Final scoped native/typed-SDK/HTTP regressions after that correction: **48 passed, zero skips**, exit 0 (4.25 seconds). New actual-server coverage proves unavailable setup is false, traversal/URL paths still fail as ValueError, a valid document still refuses conversion as RuntimeError when its engine is absent, and no output/private job survives. Required-engine positive conversion continues to run actual Pandoc and independently inspect DOCX/TXT artifacts. Whole-repository CI on this corrected source remains a separate mandatory check; no failed old job was rerun or relabeled as passed.

The same ordinary target L0 runner was then executed on a SHA256-byte-identical temporary source context on a normal Linux filesystem: required-engine run **20 PASS / 0 FAIL / 0 SKIP**; intentionally unavailable-engine run **6 protocol PASS / 0 FAIL / 1 explicit native SKIP**. The latter is only an unavailable-runtime protocol negative and does not establish conversion acceptance. Both real servers were terminated/reaped and their unique contexts/artifacts removed.

An intermediate required-engine run directly in this platform's mounted workspace failed with a real `PermissionError` from the no-clobber `os.link` publication. Independent owned probes confirm the workspace mount rejects hardlinks (errno 1) while the ordinary temporary filesystem supports them with identical inode readback. That environment failure is preserved; publication was not weakened. Runtime `WORKSPACE` must reside on a filesystem supporting hardlinks, as in the actually passed Docker image. Persistent source remains in the workspace; only the byte-verified runtime test context used the ordinary temporary filesystem.
