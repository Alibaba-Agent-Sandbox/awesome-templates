# Verification: HTML/PPTX/Writer PDF preparation

Date:2026-10-20. Result:PARTIAL. Scope: scoped uncommitted document-tools1.1 runtime, image, controller, tests and bilingual docs on baseca3118e5123e7ce2ae2e43e2a8a05c88ecf3653d.

Actual pinned Debian Pandoc3.1.11.1+ds-2 with data3.1.11.1-3 and liblua5.4-0 5.4.7-1+b2:59native cases PASS/1PDF SKIP in2.19seconds. Original content/path/process regressions remain. New guarded HTML and native PPTX conversions independently parse XML/text/full hashes. An additional actual H1-only slide fixture retains random marker, bold text, Unicode and list items. Rejected resource-bearing HTML never reaches a native reader. No mocked PDF is counted.

The operator lacks LibreOffice. Required actual PDF execution, current-head CI, image and Express1.1acceptance are pending. Historical1.0receipts remain immutable and cannot qualify1.1. Writer is required in dedicated Debian CI, which fails rather than skipping if absent; the external controller requires genuine independently parsed PDF pages and nonce text. No cloud resources were created for these source checks.

Commands: python -m pytest -q document-tools/test_commands.py with actual DOCUMENT_PANDOC_BINARY, DOCUMENT_PANDOC_DATA_DIR and library path. Full source/spec/docs checks and current revision hashes will be recorded after final preparation. Actual package selection is supported by [Debian writer-nogui](https://packages.debian.org/trixie/libreoffice-writer-nogui); native flags/profile ownership follow [official start parameters](https://help.libreoffice.org/latest/en-US/text/shared/guide/start_parameters.html). Controller dependency pypdf6.21.1public wheel SHA256553e2d42f5bb3bb2a785a7d3de8ef90bb7df74b5413eff5a7b4388007ea9254b.

Source checks PASS:56spec-tool cases in12.616seconds; whole-catalog strict checker0failures;150Markdown documents0link failures; git diff --check clean. Source-only validation does not establish PDF, image or Express acceptance.

## First required native CI failure and correction

Initial head0eebec8dbbdddcd83be03a0a4affec7968c70449: actual Debian CI61PASS/1FAIL. Writer PDF exited81 on its fresh private profile, exposing that direct soffice.bin bypassed upstream startup handling. The [pinned official launcher](https://github.com/LibreOffice/core/blob/libreoffice-25.2.3.2/desktop/scripts/soffice.sh) executes oosplash; its [startup source](https://github.com/LibreOffice/core/blob/libreoffice-25.2.3.2/desktop/unx/source/start.c) handles native restart exits. Use the installed official launcher with the same private HOME/XDG/temp/UserInstallation and shared deadline/group ownership instead of adding unchecked success or retries. Initial failed CI is retained; actual corrected PDF remains required. Subsequent operator native+authenticated HTTP tests61PASS/1PDF SKIP in3.36seconds; this does not prove the PDF fix.

Initial actual SDK-created native step attempt also failed after9HTTP assertions at the PDF/Writer stage. Independent owned sandbox/template cleanup PASS; the failed full-http-steps receipt remains in template evidence. Corrected native PDF regression additionally verifies a caller HOME sentinel remains byte-identical with no added caller files. No old failing runtime is relabeled as corrected acceptance.
