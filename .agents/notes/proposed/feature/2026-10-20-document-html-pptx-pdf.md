# Decision: Bounded HTML, slides and headless Writer PDF

Status: proposed

## Problem

[Issue55](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/55) requires Markdown/HTML to office documents, PDF and slides. Existing1.0 only implements Markdown/DOCX/TXT and cannot complete that scope.

## Decision

Extend the existing compatible convert command in1.1 with explicit HTML input and PPTX/PDF outputs. Reject resource-bearing HTML before native reading, retain the bounded metadata-free/image-free/raw-free Pandoc AST and fixed writers. Generate PDF only from that validated generated DOCX using exact Debian headless Writer, a private profile and shared operation deadline. Retain no-clobber outputs, descriptor snapshots, resource limits and owned process cleanup. Require fresh current-version native/image/Express receipts before qualification.

## API Design

Append optional input_format="markdown"|"html" to convert; retain path/format/deadline defaults. output_format adds pptx and pdf. Add office_version and document_extended_smoke. Existing result remains output_path/output_format/bytes/sha256. Inputs are UTF-8 text≤1MiB, outputs≤8MiB, command_timeout1–60seconds. HTML only permits balanced text tags and explicit safe attributes; images, scripts, styles and resource attributes fail before Pandoc. PPTX validates1–100native slide XML entries; PDF signature is supplemented by independent external pypdf page/text/nonce parsing. Increase sandbox memory to4096MB; Writer gets2GiB address space/60–61CPU seconds, Pandoc retains1GiB/30–31seconds. Each conversion owns HOME/XDG/temp/UserInstallation; no caller profile is adopted.

## Alternatives considered

- Arbitrary HTML/office uploads: adds macros, external fetches and uncontrolled parsers beyond bounded text.
- Markdown-rendered browser screenshots: do not implement actual office/slide conversion.
- TeX PDF engine: unnecessary additional engine/font surface when fixed Writer accepts the generated DOCX.
- Shared persistent office process/profile: risks caller state, ownership and concurrent conversion interference.

## Dependencies

Pandoc3.1.11.1+ds-2/data3.1.11.1-3, headless LibreOffice writer/core/common4:25.2.3-2+deb13u8, DejaVu2.37-8 and NotoCJK1:20240730+repack1-1. Retain native distribution copyright notices. Independent controller pypdf6.21.1; no model credentials, display, GPU or privileged daemon. Public SDK server source remains the historical qualified immutable pin; no SDK contract changes.

## Test Strategy

Actual pinned Pandoc tests parse full DOCX/TXT/PPTX bytes and markers. HTML negatives forbid any native-reader invocation. Required Debian CI installs actual Writer and independently parses fresh PDF text with pypdf; a missing engine fails. Full HTTP controller independently uploads random Markdown/HTML, downloads each format, verifies SHA/structure/content/original inputs and removes owned files. Image and native platform-step attempts must retain exact source/package provenance and independent cloud cleanup; source-only tests do not qualify them.

## Acceptance criteria

- Native and authenticated HTTP regression suites plus source/docs checks pass.
- Actual pinned Writer produces independently parsed random PDF content with owned profile cleanup.
- Latest-head mandatory CI and real L1 pass.
- Current1.1actual Express image and step capability are verified with CLI/SDK and independent cleanup, preserving failures as history.
- Both README languages, design, manifest, catalog and evidence agree; actual PR merges before Issue55closes.

## Evidence

[Verification](../../../evidence/verify/2026-10-20-document-html-pptx-pdf.md).
