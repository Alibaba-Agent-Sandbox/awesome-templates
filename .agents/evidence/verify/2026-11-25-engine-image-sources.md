# Verification: Database/document image dependency sources

- Date: 2026-11-25
- Base: `52f7653bda0b6c6406207e28095ee09a87cb5018`.
- Result: PARTIAL — original product failures and actual base layout verified; repaired L1, HTTP and current-head CI remain pending.
- Issue: [314](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/314).

## Actual original-image failure

The unchanged main Dockerfiles were dispatched through the existing [image workflow run45554543255](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/45554543255), selecting only `dev-services,document-tools`, `export_images=false`.

Both jobs pulled `fc-e2b-registry.cn-hangzhou.cr.aliyuncs.com/runtime/base:v0.0.49@sha256:baa760a43ee80b4d387d55269679c4bb572a4c333bd9b3c521aed6fe04b550bc` successfully. Apt fetched current Aliyun-mirrored trixie, trixie-updates and trixie-security metadata.

- [dev-services](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/45554543255/job/139003443394): apt exits 100; exact 17.11 server, client and libpq5 packages are not found.
- [document-tools](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/45554543255/job/139003443468): apt exits 100; exact u9 common/uiconfig/base-core dependencies conflict with the u12 candidate.

These are actual dependency-resolution failures after a successful base pull. Neither a registry/network failure nor the native CI container is substituted for that proof.

## Read-only actual base inspection

An anonymous OCI manifest/layer stream inspection verified the manifest digest and both compressed layer digests/sizes against that exact L1 base. It did not extract a filesystem or execute a container. The [sanitized file inventory](2026-11-25-engine-image-base.json) records:

- Debian 13 / trixie, `DEBIAN_VERSION_FULL=13.4`.
- Only `/etc/apt/sources.list.d/debian.sources`; no separate sources.list or other source entries.
- Rolling Aliyun-mirrored Debian and Debian-security URIs for the three trixie suites.
- `Signed-By: /usr/share/keyrings/debian-archive-keyring.pgp`; `.gpg` is a symlink to that `.pgp` keyring.

The recipe therefore replaces the actual sole source file, preserving the real archive keyring. It does not add a snapshot alongside an active rolling entry.

## Candidate scope and pending checks

Only these two recipes' apt sources and patch versions change, with necessary bilingual source explanations, design and owner records. Original base/server/engine pins, commands, E2E assertions, catalog experimental status and provider receipts stay unchanged. The separately documented [native CI preparation](2026-11-25-offline-ci-apt-snapshot-remote.md) is reused without weakening tests.

| Preparation check | Result |
| --- | --- |
| `python scripts/test_spec_tools.py` in the existing project test environment | PASS; 60 tests, including expected invalid-fixture controls |
| `python scripts/check_template.py --all` in that environment | PASS; zero non-conformant templates |
| `python scripts/check_docs.py` | PASS; 236 documents, zero failures |
| Modified/new Markdown target and seven-section decision/status checks | PASS |
| Both recipe source `printf` commands executed with output captured, plus `sh -n` | PASS; two valid signed archive stanzas per recipe, no system sources changed |
| Compare the recipes with their original bytes after removing the single new source-setup block | PASS; exact original base, dependencies and every later instruction remain |
| `git diff --check` | PASS |

The [exact context manifest](2026-11-25-engine-image-contexts.json) records every included source file hash plus each prepared Dockerfile hash after the existing workflow's default FROM substitution. The temporary verification branch must match these product contexts and must not alter the final image workflow or selector.

Actual repaired L1 builds, unmodified image HTTP E2Es and complete remote CI remain pending. A later verification gets its own dated evidence; no pending result is a pass.

## Cleanup and limits

The failed baseline run pushed/exported no image and created no cloud resources. Hosted runners own their local failed build cache. No cloud Sandbox, registry repository, model request or provider qualification was created. The candidate currently has no repaired-image or HTTP acceptance claim.
