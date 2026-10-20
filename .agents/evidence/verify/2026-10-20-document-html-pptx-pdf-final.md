# Verification: actual document HTML/slides/Writer PDF

Date:2026-10-20. Result:PASS for current native/runtime/image/Express. Final latest-head CI after qualification metadata and normal merge remain required. [Issue55](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/55).

## Runtime and native correction

Document-tools1.1.0 runtimeb887bb1d8feb80cc47444c17ba1d7f466285bfd8. Pinned Pandoc3.1.11.1+ds-2/data3.1.11.1-3, headless LibreOffice writer/core/common4:25.2.3-2+deb13u8 and pinned DejaVu/Noto fonts. Guarded Markdown/HTML to actual DOCX/TXT/PPTX/PDF keeps the existing API defaults, descriptor snapshots, AST filtering, bounded resource/deadline/group cleanup and no-clobber publication. Native Writer receives only validated generated DOCX with a private HOME/XDG/temp/profile.

Initial required Debian CI61PASS/1FAIL exposed direct soffice.bin exit81 on a fresh profile. The fixed official launcher handles native restart while preserving isolated UserInstallation and process ownership. The corrected required native Debian job passes, including actual independently parsed PDF/fresh text and unchanged caller HOME sentinel. The original failed CI and failed actual step receipt remain immutable. Operator source tests61PASS/1explicit missing-Office SKIP are separately scoped, not counted as PDF acceptance.

## Actual SDK-created native steps

[Full step controller](../../../document-tools/evidence/full-http-steps-2026-10-20T143722Z.json) and [official READY/CLI/SDK receipt](../../../document-tools/evidence/express-2026-10-20T143722Z.json):36PASS/0FAIL/0SKIP. Exact source b887bb1, actual Sandbox.create, genuine pinned Pandoc/Writer, independent full downloaded bytes/SHA256, DOCX heading/bold/XML, PPTX slide XML, pypdf pages/fresh nonce/Unicode/text and unchanged Markdown/HTML. Own files removed and known sandbox/template absence independently confirmed.

## Actual immutable image

[Explicit successful export39440349307](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/39440349307), artifact12275216256. [Image proof](../../../document-tools/evidence/image-http-2026-10-20T150549Z.json) verifies archive SHA25691f8aa4bdef345dda13c5d81c839bbf043acadd3f84c2ae873f577551e9871a0, actual source/non-root context, common injected servere2cb27e24fde0a67112f82b8d44af463445a5d1a and owned private-registry digest before registration and after runtime. [SDK creation/CLI/SDK receipt](../../../document-tools/evidence/express-2026-10-20.json) passes genuine native smoke and full HTTP36PASS/0FAIL/0SKIP. Sandbox/template/registry absence independently confirmed; no cleanup acknowledgment is substituted for readback.

Controller SHA2568ade2026f1ffb114fc63f33d4229007fcf3c2a5f92d937ca38eb23ff6ca85085; commands7b959fed8bc731e3fdeeaef073d0f0338f285b3607ceb47ff3692a6530015915. Independent pypdf6.21.1 is operator/controller-only. Installed native client matches all340Python source files at SDKd4d93e8cbb986f33a8868f7a4139ed0edb49eaba, installed from local source (not editable). Paired public installation is documented separately. The image server and standalone fallback are not conflated.

## Source checks, retention and limits

Initial source checks56spec-tool cases, strict catalog and150Markdown links passed; final integrated checks/current-head CI remain required and will be recorded separately. Image transport uses a GitHub-digest-verified compressed public ZIP in bounded anonymous RAM; the original archive/member/source/non-root/real disk-reserve checks all run unchanged. Cloud success independently confirms cleanup, then removes the large local image cache. Original failures, exact versions/hashes, source and upstream artifact IDs remain; no credentials/raw sensitive logs are published.

No model is needed; model_acceptance=NOT_RUN in image receipts is correct for this deterministic native product. No GUI, macros, uploaded office files, arbitrary filters/options, remote resources or unrestricted HTML support is claimed. Historical1.0cloud receipts do not certify1.1.
