# Verification: Actual GitHub offline engine installation

- Date: 2026-11-25
- Tested head: `47289e325424c038da809517d0c45105549b6d60`
- Result: PASS for the two repaired apt/native jobs. Overall current-head CI and PR merge are separate gates.
- Run: [e2e 45550292616](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/45550292616).

## Observed results

| Job | Actual result |
| --- | --- |
| [dev-services-offline](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/45550292616/job/138989603520) | PASS; signed archive preparation, exact PostgreSQL 17.11/Redis 8.0.2 installation, 12 native tests, and the existing non-root local HTTP E2E all succeeded |
| [document-tools-offline](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/45550292616/job/138989603564) | PASS; signed archive preparation, exact LibreOffice u9/Pandoc installation, 62 conversion/SDK/HTTP tests, and the existing local HTTP E2E all succeeded |

Both job logs show InRelease metadata fetched from the exact `20261112T000000Z` Debian, Debian-updates and Debian-security archives. Apt completed without an unauthenticated/trusted override, then installed the unchanged reviewed engine versions. The original failures and local network errors remain in the [preparation evidence](2026-11-25-offline-ci-apt-snapshot.md).

The other five jobs in this tested-head e2e run also completed successfully: media-tools-offline, documentation, local-e2e, express-cli-contract and template-v1-contract. The unchanged image planner succeeded and selected no image rebuild for this scope; its image-build job was skipped by the existing rules. The existing explicit-authorization workflow also passed. Later documentation commits require their own current-head remote checks before merge.

## Scope and cleanup

These are actual GitHub-hosted Debian container jobs with native engines and local HTTP services. They establish the CI preparation repair and preserve the existing assertions. They do not establish a template image rebuild, cloud deployment or new model/provider qualification. GitHub completed both jobs' container cleanup. No task-created cloud resources exist.
