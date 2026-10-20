# Decision: publish independent OCR platform-step acceptance

Status: proposed

## Problem

[Issue 57](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/57) requires actual image-to-text delivery on Express. The user also requests testing genuine platform steps. An image receipt does not prove this build mode.

## Decision

Publish new immutable receipts for OCR 1.0.1 built by actual Express steps. Preserve all earlier image receipts and failed attempts. Document the public step operation and distinguish its fixture smoke from the additional full HTTP controller.

## API Design

No runtime or public command changes. Use the existing preparation, native CLI submission, official readiness, CLI/SDK smoke and independent resource-absence readbacks. Run the unchanged OCR controller against the created sandbox before deleting owned resources.

## Alternatives considered

Do not infer step success from source preparation, CLI submission or an image pass. A successful readiness response plus independently retrieved OCR artifacts is required.

## Dependencies

OCR source b232ed7bb1d516154ec15e3b8ec8669c164a7f8b, base v0.0.49, server e2cb27e24fde0a67112f82b8d44af463445a5d1a, native CLI 0.3.0 and reviewed SDK. Values and private ownership journals remain outside the repository.

## Test Strategy

Check both exact-version receipts, 19 complete external HTTP assertions with no failures/skips, CLI/SDK recognition and independent sandbox/template cleanup. Check strict template metadata and document links. No model assertion is needed for native Tesseract OCR.

## Acceptance criteria

- New step receipts identify exact inputs and build mode, pass all 19 HTTP assertions and confirm owned cleanup independently.
- English and Chinese operations and Verified tables distinguish image, step smoke and full HTTP scopes.
- Current-head CI, normal merge and remote readback complete the publication.
