# Verification: Community QR replacement

- Date: 2026-11-10
- Base: `575a5ca3fc9c78762d17ad04ac197eaa4e8bffaa`
- Scope: root README translations, community image, shared UI where applicable, and engineering records.
- Result: BLOCKED — scoped checks pass; existing required CI dependency failure tracked in Issue304.

## Verified source

The maintainer's JPEG is 436 × 434 pixels. Independent ZXing decoding yields the updated DingTalk invitation used by the clickable links. The group name, number and release announcement are unchanged. Preserve the original image bytes; old verification records remain historical.

## Checks

- PASS: Scoped document and image checks; existing PR303 CI blocker remains separate.
- PASS: both README paths resolve to the byte-identical JPEG; independent ZXing decoding matches the updated clickable URL. Old PNG references are absent from the current README/UI entries.
- PASS: group number, release version/date and existing relative Markdown links preserved; `git diff --check`.
- Image SHA256: `e7951550c99f07e60366801911577ecc29ff81966a7a36a172a10bca39573b39`.
- No additional runtime tests needed for this asset/link replacement; required remote CI is not bypassed.

## Limits

No runtime/package release or cloud resources; no DingTalk membership action. Remote CI and deployment are verified separately. Template PR303 was already blocked by unavailable pinned LibreOffice dependencies (Issue304); this asset change does not modify that workflow or its dependencies.
