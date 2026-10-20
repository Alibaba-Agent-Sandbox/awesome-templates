# Verification: HTML/PPTX/Writer PDF preparation

Date:2026-10-20. Result:PARTIAL. Scope: scoped uncommitted document-tools1.1 runtime, image, controller, tests and bilingual docs on baseca3118e5123e7ce2ae2e43e2a8a05c88ecf3653d.

Actual pinned Debian Pandoc3.1.11.1+ds-2 with data3.1.11.1-3 and liblua5.4-0 5.4.7-1+b2:59native cases PASS/1PDF SKIP in2.19seconds. Original content/path/process regressions remain. New guarded HTML and native PPTX conversions independently parse XML/text/full hashes. An additional actual H1-only slide fixture retains random marker, bold text, Unicode and list items. Rejected resource-bearing HTML never reaches a native reader. No mocked PDF is counted.

The operator lacks LibreOffice. Required actual PDF execution, current-head CI, image and Express1.1acceptance are pending. Historical1.0receipts remain immutable and cannot qualify1.1. Writer is required in dedicated Debian CI, which fails rather than skipping if absent; the external controller requires genuine independently parsed PDF pages and nonce text. No cloud resources were created for these source checks.

Commands: python -m pytest -q document-tools/test_commands.py with actual DOCUMENT_PANDOC_BINARY, DOCUMENT_PANDOC_DATA_DIR and library path. Full source/spec/docs checks and current revision hashes will be recorded after final preparation. Actual package selection is supported by [Debian writer-nogui](https://packages.debian.org/trixie/libreoffice-writer-nogui); native flags/profile ownership follow [official start parameters](https://help.libreoffice.org/latest/en-US/text/shared/guide/start_parameters.html). Controller dependency pypdf6.21.1public wheel SHA256553e2d42f5bb3bb2a785a7d3de8ef90bb7df74b5413eff5a7b4388007ea9254b.

Source checks PASS:56spec-tool cases in12.616seconds; whole-catalog strict checker0failures;150Markdown documents0link failures; git diff --check clean. Source-only validation does not establish PDF, image or Express acceptance.
