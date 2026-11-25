# Verification: Actual rebuilt engine images and HTTP tasks

- Date: 2026-11-25
- Result: PASS for the tested product contexts, normal CI and actual image HTTP verification below. A later records-only head still requires its current-head checks before merge.
- Product source: `bb1c3212049640a7e7628e5961d90ea374171194`, [PR315](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/315).
- Temporary verification source: `626a0434aa0c61786badf1f143ad6b1777078f83`. Its [verifier](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/blob/626a0434aa0c61786badf1f143ad6b1777078f83/.agents/evidence/verify/2026-11-25-engine-image-http.py) and workflow addition are on an unmerged branch, not the repair PR.

## Unchanged actual base and native image checks

The normal [L1 run45555956525](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/45555956525) selects exactly the two changed contexts. Both actual images build successfully from the original Provider base digest `sha256:baa760a43ee80b4d387d55269679c4bb572a4c333bd9b3c521aed6fe04b550bc` and fetch InRelease metadata from the signed `20261112T000000Z` archives.

| Job | Actual result |
| --- | --- |
| [dev-services L1](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/45555956525/job/139008061497) | PASS; original server 0.4.0a6, non-root workspace write/read/removal, exact engine version and real authenticated database self-test |
| [document-tools L1](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/45555956525/job/139008061499) | PASS; original server 0.4.0a6, non-root workspace write/read/removal, all four native Pandoc/Writer smoke commands |

The normal [e2e run45555956437](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/45555956437) completed all seven jobs successfully: contract checks, documentation, database/document/media native jobs and complete local E2E. The explicit-authorization workflow also passed. These native/function checks are distinct from the HTTP proof below.

## Actual image HTTP verification

The [controlled verification run45556703477](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/45556703477) dispatches only these two contexts with `export_images=false`. Its added HTTP step is not merged. The product directories have no Git diff from the repair source, and each job independently compares every prepared-context file against the committed [context manifest](2026-11-25-engine-image-contexts.json).

| Actual image | Context identity and observed result |
| --- | --- |
| [dev-services HTTP](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/45556703477/job/139010454988), image `sha256:83aa70fcb63acdf27eb22b5277989c5721629a5b7b276d4ad7c4484b3ade1fc1` | All 22 files match; source context `36e062ef66ec73cb02c24cd4a05e92e7ee83a2151046bdcc7de0f9e54a23d266`; original required-engine E2E exits 0 without skips/failures |
| [document-tools HTTP](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/45556703477/job/139010454911), image `sha256:2226ad1d1e160c8c80ed3656aca1d9fab8bff917b87ca65e45b45450b89a476f` | All 24 files match; source context `495c7bc4652b09f2d37512e2ce678ef315e586bcd907e0df22dc5aa4f40bf283`; original required-engine E2E exits 0 without skips/failures |

Both jobs start the image's real manifest startup command and execute its readiness command, using the default non-root image user and only a loopback HTTP port. Installed-package queries verify the original exact engine versions. The live image also has the expected dated source stanzas, keyring and source-identical command module.

The unchanged database controller performs real authenticated SQL/Redis read/write, restart/persistence, invalid-command controls, owned-process stop and nonce-data deletion with an independent HTTP absence check. The unchanged document controller uploads unique Markdown/HTML, converts and downloads DOCX/TXT/PPTX/PDF, checks complete-byte hashes, independently parses document/PDF content and confirms the fresh nonce and Chinese text.

## Cleanup verification and review

After each original controller, independent reads confirm the workspace's top-level name set is unchanged apart from Python cache and no PostgreSQL, Redis or Writer process names remain. This is that bounded check, not a complete filesystem/process audit. The owned container is then force-removed in `finally`, with an independent local Docker NotFound result.

Independent review caught a temporary verifier cleanup gap before dispatch: Docker creation/ID validation had been outside `try`. Creation is now protected; the UUID name and ownership label limit cleanup, and Docker operations have deadlines. Two local mocked failure controls verify malformed creation output still cleans an owned container and foreign ownership is refused. These controls establish only harness cleanup behavior; they are not image acceptance.

No image was pushed/exported and no cloud Sandbox, database, model request or registry repository was created. The temporary verification workflow addition is not merged; the selector is unchanged. Original failed L1 and local network observations remain in the [preparation record](2026-11-25-engine-image-sources.md). Both catalog entries remain experimental and historical provider receipts are unchanged; this is not renewed cloud/provider qualification.
