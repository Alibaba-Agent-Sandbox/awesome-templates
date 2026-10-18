# Decision: bounded CPU Tesseract image OCR

Status: proposed

## Problem

[Issue 57](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/57) requests image-path to text OCR, real Express verification and documentation. The keyless CPU Tesseract slice can be implemented without waiting for a model account or GPU.

## Decision

Install official Tesseract 5.5.0 through exact Debian engine/English-data/Leptonica package versions, with hashlocked Pillow 11.3.0 wheels. Expose typed diagnostics, one workspace image-to-text task and actual fixture smoke. Keep source, image and supplemental cloud evidence distinct from canonical deploy L2; retain experimental status and empty tested_on until that gate is actually met.

## API Design

`ocr_version`, `ocr_setup_check`, `ocr(image_path: str)` and `ocr_smoke`. No executable/flags/language/network parameter is exposed. Restrict path traversal using directory FDs/no-follow opens, encoded bytes, PNG/JPEG frame/dimension checks and private normalization. Fixed argv writes private text/TSV with bounded output and owned cleanup. Success publishes mode-0600 files under a fresh mode-0700 workspace directory. Original HOME/input remain unchanged. See [design](../../../../docs/design/ocr.md) for exact limits and public errors.

## Alternatives considered

A remote OCR model introduces unnecessary credentials and nondeterministic availability. Generic shell wrapping expands the public interface; fixed named argv avoids that. Python preexec_fn is unsafe with a threaded server, so an isolated exec wrapper sets native rlimits. Uploaded archives/PDF add parser and extraction scope and are deferred. A static marker or expected text returned by a fake executable is not OCR acceptance; actual recognition and independent result retrieval are required.

## Dependencies

Pinned Debian critical packages, official hashlocked Pillow wheels, source-built server wheel/fixed SDK source, non-root writable workspace and Linux WNOWAIT/resource support. The base's transitive OS libraries are repository-resolved. No cloud/model secrets enter the image. Native diagnostics used only private extracted distribution packages, not a host-wide install.

## Test Strategy

Real process success/error/deadline/cancellation descendants and foreign-group controls; bounded diagnostics; path/symlink/FIFO/encoded-byte/pixel/frame checks; normalization and TSV validation; private environment/resources/artifacts; actual authenticated HTTP startup forms; actual Tesseract fixture recognition. Independent source HTTP acceptance synthesizes random digits, retrieves TXT/TSV, checks hashes/meaningful words/confidence/bounds and unchanged input, then blank-image negative control and owned cleanup. Synthetic executable fixtures test failure/privacy mechanics only.

## Acceptance criteria

- Complete v2 template, English/Chinese usage, design and matching experimental catalog metadata.
- Actual pinned engine recognizes meaningful fixture pixels and independent output files.
- Input/output limits, argv-only invocation, private temporary/result ownership and managed process cleanup have observable regressions.
- Actual L1 image smoke and supplemental changed-image cloud evidence remain pending until run; canonical deploy L2 is not inferred from them.

## Evidence

[Verification](../../../evidence/verify/2026-10-16-ocr-runtime.md). Issue 57 remains open for remote/canonical delivery gates.

Image-install follow-up: [first actual L1 failure and minimal offline-wheel repair](../../../evidence/verify/2026-10-16-ocr-image-install.md).
