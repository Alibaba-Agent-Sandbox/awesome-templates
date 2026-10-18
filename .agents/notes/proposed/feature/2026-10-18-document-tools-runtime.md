# Decision: Deliver a bounded Pandoc text conversion slice

Status: proposed

## Problem

[Issue 55](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/55) remains unimplemented despite its CPU-only Pandoc slice requiring neither model credentials nor hardware. The survey explicitly permits pure text conversion first; broader office/PDF/slides functionality remains separate work. Arbitrary Pandoc arguments and untrusted embedded resources would create avoidable file/network authority.

## Decision

Add a standalone `document-tools` spec-v2 experimental template for Markdown → DOCX/TXT, with exact Debian code/data pins, typed fixed argv, descriptor snapshots, no-clobber artifacts, native resource/process limits, bilingual documents, actual codec-independent document validation and scoped CI. A sandboxed GFM parser emits JSON; an explicit AST gate rejects Image/Raw nodes and unsafe links, caps complexity, removes metadata, then passes only the validated document to the fixed writer.

## API Design

New commands: `document_version`, `document_setup_check`, `convert` and `document_smoke`. See [the design](../../../../docs/design/document-tools.md). Existing public server/client contracts do not change. General shared shell/files authority remains unchanged; the restrictions apply to this named conversion interface.

Path/size/UTF-8 validation precedes native availability checks, so malformed input keeps its argument error even on a host without Pandoc. Every valid conversion then checks the actual executable pin within the same total deadline before native parsing; missing/wrong engines cannot produce successful artifacts.

## Alternatives considered

Block all coding on canonical cloud configuration: rejected; native document behavior can be implemented and verified independently. Claim the whole original office task complete from Markdown conversion: rejected; Issue 55 stays open. Run arbitrary `soffice`/Pandoc argv or let the DOCX writer resolve untrusted images: rejected. Use DOCX `--sandbox` with Debian's non-embedded-data package: actually attempted and failed because internal package templates cannot be found; retain sandbox parsing and an application AST gate instead of misrepresenting the writer boundary. A 512 MiB address-space cap also failed actual Haskell OS-thread startup; the final bounded 1 GiB virtual address space plus 256 MiB heap and two runtime capabilities fit the 2 GiB sandbox budget. Allocator arenas are capped at two.

## Dependencies

This independent branch is stacked on [OCR PR 103](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/103), exact base `a4a18b0dbb18a18ccf5e2d5c113454bff9319bc4`, and does not depend on the media-tools branch. Exact Debian packages are `pandoc=3.1.11.1+ds-2` and `pandoc-data=3.1.11.1-3`; their different versions were verified rather than guessed. Public server fallback source: `e2cb27e24fde0a67112f82b8d44af463445a5d1a`. No credential or external service is required.

## Test Strategy

Use actual extracted Debian native packages in source tests; generated Markdown includes headings, bold, list and Chinese text. Inspect ZIP/document XML independently; compare exact returned size/hash to downloaded files. Execute authenticated typed SDK and external required-engine HTTP paths; verify original input and exact owned cleanup. Run actual native nonzero/timeout/redirected-descendant and diagnostic limits, unsafe input negatives, checker/spec-tools/link/secret checks. Keep L1 image and canonical L2 evidence separate.

## Acceptance criteria

- Source native/SDK tests and required-engine HTTP checks pass without missing-engine skips.
- Independent source review has no unresolved blocking finding.
- Exact Docker image and non-root packaged document smoke pass.
- Canonical deploy/CLI/SDK smoke and strict cleanup pass before provider receipts/promotion.
- Required latest-head CI/review and actual merge state are verified.
- Broader Issue 55 stays open for HTML/PDF/slides/LibreOffice work.

## Evidence

[Verification record](../../../evidence/verify/2026-10-18-document-tools-runtime.md).
[Actual image and native CI confirmation](../../../evidence/verify/2026-10-18-document-tools-ci-confirmation.md).
