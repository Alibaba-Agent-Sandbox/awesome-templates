# Verification: Delivered public package prerequisites for template guidance

- Date: 2026-11-25
- Result: PASS for the public package prerequisites. This records-only closing head still requires its own remote checks and normal PR merge.
- Scope: the existing root/shared template guide correction in [PR313](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/313). No user guide, template/runtime or CI changes are made by this receipt.

## Execution ownership and evidence

The root agent executed the fresh public npm installation, downloaded-binary checks, alias/local-provider tests and public Python installation/HTTP checks summarized below. This receipt's author reviewed those completed result records and the remote workflow outcomes; it did not repeat their runtime commands. Earlier preparation/failed checkpoints remain unchanged.

Permanent owner evidence: [CLI public alpha.1 release](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/blob/6a1dd2287a47d501f2752777d8edfb3d1d665660/.agents/evidence/verify/2026-11-25-cli-060-alpha1-public-release.md) and [Python public 0.5.0a0 delivery](https://github.com/Alibaba-Agent-Sandbox/python-sdk/blob/92233621515cae8f294cd5b6e63508ed31dcb321/.agents/evidence/verify/2026-11-25-python-050a0-public-delivery.md).

Reviewed root result records: `public-cli-alpha1-npm-result.json`, `public-cli-alpha1-binary-result.json`, `public-cli-alpha1-npm-asset-result.json`, `cli-alpha1-final-release.json` and `public-python050-result.json`. Public artifact identities and CI links below make the publication boundary explicit.

## CLI 0.6.0-alpha.1: actual public consumers

The [GitHub preview release](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/releases/tag/v0.6.0-alpha.1) is public, `draft=false`, `prerelease=true`, published at `2026-11-25T07:14:10Z`. Its twelve assets comprise five platform binaries and matching checksums, plus the tested npm archive and its checksum. The [five-platform build run](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/actions/runs/45566018697) has all five binary jobs successful. The [npm publication run](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/actions/runs/45566546338) successfully publishes and attaches the tested npm artifacts; its optional credential-diagnostics job is skipped.

| Root's actual public check | Observed result |
| --- | --- |
| Fresh installation from the official npm registry | PASS; installed artifact contract and actual alias/mixed-alias local-provider checks pass |
| Public GitHub Linux x64 executable | PASS; checksum and executable artifact contract pass, including actual alias/mixed-alias local-provider checks |
| Public npm bytes versus tested GitHub npm archive/checksum | PASS; identical SHA256 `1b304054f38de2e46e8e4fa78527c708968ae51690b8257279840ba3f726dd0b`; npm SHA1/SHA512 metadata also matches the downloaded bytes |
| Public Linux x64 payload | SHA256 `db798f6eec60fb67a1d8cad4b80148c0fb8475bb37ff25c3bb80294f6106ce9c`, matching the uploaded checksum |

Each public consumer's local-process Provider suite reports 15 passed, 0 failed and 3 declared capability skips (pause/resume, process listing and port URL). These are local-process contract results, not cloud-provider or all-feature acceptance.

Public sources: [npm version metadata](https://registry.npmjs.org/@agent-sandbox%2fcli/0.6.0-alpha.1), [exact npm tarball](https://registry.npmjs.org/@agent-sandbox/cli/-/cli-0.6.0-alpha.1.tgz), [Linux x64 release asset](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/releases/download/v0.6.0-alpha.1/abx-0.6.0-alpha.1-linux-x64). npm `next` is `0.6.0-alpha.1`; npm `latest` remains `0.5.10`, and GitHub latest stable remains `v0.5.10`. The guide's explicit preview pin selects the delivered command contract without promoting it to stable.

## Python client/server 0.5.0a0

Root's actual [public Python publishing run](https://github.com/Alibaba-Agent-Sandbox/python-sdk/actions/runs/45554059881) succeeds. Fresh installation verifies base-client-only use without a local server, `pip check`, then the matching `[server]` extra and another `pip check`; both installed versions are `0.5.0a0`. The root public-installed runtime check acknowledges the owned listener, matches 58 server source files to the public wheel and verifies both raw HTTP and SDK round trips for 0 and 8388608 bytes.

The four official public artifact identities already independently matched the inspected candidates in the [earlier alpha.1 prerequisite record](2026-11-25-cli-alpha1-template-guidance.md). Public metadata: [client](https://pypi.org/pypi/agent-sandbox-client/0.5.0a0/json), [server](https://pypi.org/pypi/agent-sandbox-server/0.5.0a0/json). These installation/local HTTP results do not create another cloud deployment claim.

## Preserved initial failures

- The initial exact npm archive request returned HTTP404. Its original root log `cli-alpha1-public-npm-initial-archive404.log` is retained, SHA256 `27ef76b359bc73508fbcd2cc52fd4025badbc501b4ef8c899d98a12af2b22771`. Later successful full public download and byte-identity checks supersede that availability checkpoint without erasing it.
- The first fresh-install CA probe failed with a nonzero npm installation result. `cli-alpha1-public-npm-first-install-ca-error.log` is retained, SHA256 `3f12d4249bad4c98fbefde42a0489604c5a3a0a3ee0fe03ae5d7dc374b9da442`. The successful retry preserves the existing CA settings; TLS verification was not disabled. This is recorded as a probe correction, not a product TLS change.
- The earlier withdrawn alpha.0 and prepublication checkpoint records remain historical. No failed observation is rewritten as a pass.

## Closing boundary

The public-package prerequisites of the guide are delivered. The previous documentation head `d110e47066e2250769dd68559f36e7a179443148` has 10 successful checks and the unchanged docs-only image-build skip; that does not replace checks on this final records-only head. The guide's four user-facing files, runtime/CI and historical evidence facts remain unchanged here. The accepted documentation ADR moves to implemented with current decision/dependency wording and this receipt as its final prerequisite evidence.

No new cloud resources, model tasks or image builds were created to close these documentation records. Wider template API migration and the separate [Devin pinned-download HTTP403 Issue316](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/316) remain outside this scope; no all-catalog green or new provider qualification is claimed.
