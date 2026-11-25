# Verification: Offline CI Debian archive preparation

- Date: 2026-11-25
- Prior PR head: `aa4c32f5dce0b365c972c8de2e000817b6b77ea9`
- Result: PARTIAL — actual GitHub archive preparation and native jobs are pending.
- Scope: only apt source preparation in the required database/document offline jobs, plus this decision/evidence, record index and changelog.

## Reproduced failure and package evidence

The [PR run](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/45541557095) fails before checkout in both apt steps: PostgreSQL `17.11-0+deb13u1` is unavailable in the current index; LibreOffice u9's exact uiconfig dependency conflicts with the newer security candidate. The [earlier successful baseline](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/43290041176) used the same engine pins on 2026-11-12.

Read-only official Debian metadata fetched on 2026-11-25 confirms PostgreSQL `17.12-0+deb13u1` in current trixie and security indexes. LibreOffice u9 remains in trixie while u12 is the security candidate. The unchanged template runtime checks require PostgreSQL 17.11 and LibreOffice u9, so changing only the CI versions is insufficient.

Local archive requests could not establish availability: snapshot.debian.org returned HTTP 509; its Cloudflare endpoint returned HTTP 429, and the alternate Debian endpoint reset the connection. These are failed local network probes, not package-installation or native-test passes. GitHub's actual signed apt installation remains the acceptance gate.

## Verification commands and outcomes

| Executed check | Result |
| --- | --- |
| PyYAML parse and `sh -n` for both modified run blocks | PASS, exit 0 |
| Compare exact apt package arguments and all subsequent job steps against the prior head | PASS; unchanged |
| Compare every other job against the prior head | PASS; unchanged |
| Execute only the source-definition printf with output captured locally | PASS; valid two-stanza Deb822 output, no system sources changed |
| `python scripts/check_docs.py` | PASS; 236 current documents, 0 failures |
| Existing Markdown checker over new records, index and changelog; seven-section decision/status check | PASS; 4 files, 0 failures |
| `git diff --check` | PASS, exit 0 |

Current-head GitHub results must be checked separately before merge. The exact UTC archive selection is `20261112T000000Z` for both Debian and Debian-security. Only historical-source `Check-Valid-Until` is disabled; `Signed-By` remains the Debian archive keyring, with no trusted/unauthenticated override.

## Cleanup and limits

No cloud resources, images or services were created. This repair does not validate template image rebuilds or renew historical provider/model acceptance. Existing template Dockerfiles and all product/native version assertions remain unchanged.
