# Verification: Preview release notice and developer community

- Date: 2026-11-10
- Base revision: `e94ab308a74715982bb059b142518f7d6070c1c2`
- Scope: bilingual root READMEs and the original community QR image and this repository's engineering record.
- Environment: Linux, Node.js 22.22.2, Python 3.13.13.
- Result: BLOCKED — local documentation checks pass; required remote CI fails during existing dependency installation.

## Content and image

The original 470 × 468 PNG was downloaded from the maintainer's attachment without editing. Independent decoding resolves the supplied DingTalk join code. Its origin query parameter is 1, while the supplied clickable URL has origin 11; both retain the exact same join code. Preserve both supplied inputs.

## Validation

- PASS: Scoped documentation/image and record checks; template source and catalogs are unchanged.
- PASS: both root README languages checked for expected date/version/preview language, group number and exact original image bytes; all relative Markdown links resolve.
- PASS: `git diff --check`; seven-section note, matching proposed status and local evidence/index links inspected.
- The exact scoped files are this commit's README/image/UI changes and engineering records. Documentation checks do not establish runtime or cloud acceptance.

## Limitations and cleanup

No package release, cloud sandbox or model task is part of this documentation change. No temporary cloud resources created. DingTalk membership was not joined or authenticated. Publication is checked separately after merge.

## Remote merge gate

The document-tools-offline job fails before tests: Debian trixie cannot resolve LibreOffice 4:25.2.3-2+deb13u8. The announcement changes no workflow or template dependencies. No gate was skipped and the PR remains unmerged. Follow-up: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/304. Original failure: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/42793988288/job/129754293724.
