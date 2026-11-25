# Verification: Alpha.1 prerequisites and landed image-source integration

- Date: 2026-11-25
- Result: PARTIAL — documentation/integration checks are local; CLI alpha.1 public readback and this new head's remote checks remain required before ready/merge.
- Scope: the existing bilingual root/shared guide correction, normal main integration and accepted engineering-record lifecycle.

## Release prerequisite

The current installation examples target CLI `0.6.0-alpha.1` and Python client `0.5.0a0`. Root's independent standalone-artifact check found a missing bundled cloud SDK dependency outside the checkout for alpha.0, cancelled its npm publisher and withdrew its GitHub release to Draft. The next immutable candidate is alpha.1, tracked in [CLI Issue270](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues/270). This record attributes that artifact finding to the root release verification; it does not claim to repeat its runtime test.

Independent anonymous npm metadata reads at this checkpoint return HTTP404 for both exact alpha.0 and alpha.1 versions. No alpha.1 public availability or fresh installation is claimed. The earlier [alpha.0 preparation record](2026-11-25-current-cli-template-guidance.md) remains unchanged as history. The guide stays Draft until the actual alpha.1 public readback and owner release gates pass.

Independent official PyPI reads return HTTP200 for both 0.5.0a0 distributions. All four public SHA256 values match the previously independently inspected candidate artifacts:

| Public artifact | SHA256 |
| --- | --- |
| client wheel | `fbb37f5056fee46bd9b7bc8871c5685dd4a5b0bf2991975ef217cb23933fbd75` |
| client sdist | `5d5c877305561da65253da414016684b6444da24e3ba65e63449436230080338` |
| server wheel | `2c1ceed013d0f361f9ccb7b19339315ed25e89a8e5623a69e07d10e3080f5e4d` |
| server sdist | `25712b55cd5aed4c2b12021c8f5faa00161b3e2b1b47c98c6a1fef7b5d767408` |

Sources: [client metadata](https://pypi.org/pypi/agent-sandbox-client/0.5.0a0/json), [server metadata](https://pypi.org/pypi/agent-sandbox-server/0.5.0a0/json). This establishes public artifact identity, not another fresh-install or cloud test.

## Normal main integration

[PR315](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/315) actually merged as `93e8f831036eb50941dfe9dd027b5878772837e1` on 2026-11-25. Its final `2944956385c9df4be822088f0caa1fbed99922c1` head had all required checks successful. Its [actual image/HTTP evidence](2026-11-25-engine-image-sources-remote.md) preserves the original failures, default-base identity, exact contexts, native/image checks, strict HTTP business/artifact checks and owned cleanup. No template qualification was promoted.

The docs branch integrates that exact main by a normal two-parent merge. Only record-index and CHANGELOG overlaps needed resolution; landed Dockerfiles, template versions, CI preparation, context hashes and verification facts are preserved. The accepted offline-CI and image-source ADRs move to `implemented` with only their Status and link targets updated. Historical evidence facts and the alpha.0 preparation checkpoint are unchanged.

The remaining root/shared docs select the new exact installation targets, keep lifecycle inspection/cleanup simple, preserve existing SDK/HTTP examples and explicitly separate older template-owned CLI examples from 0.6's bound-OpenAPI interface. The broader template API migration remains outside this correction.

## Checks and limits

| Executed local check | Result |
| --- | --- |
| Existing Markdown checker over 12 changed/new documents | PASS; no local target/fragment failures |
| `python scripts/check_docs.py` | PASS; 236 documents, zero failures |
| Four Python example AST parses and exact current installation/command spellings | PASS |
| Compare landed template/catalog/CI/image-selector bytes against main93e8f83 | PASS; unchanged |
| Historical evidence and original alpha.0 preparation comparison | PASS; unchanged |
| Both accepted ADR moves | PASS; only path/Status and index links change, seven-section structure retained |
| `git diff --check` | PASS |

The normal merge's parent identities are checked before push. Complete remote CI remains a separate merge gate. Do not treat the prior docs head's green CI or PR315's accepted image contexts as this new head's completion.

No new cloud resource, image build, model task or package publication was performed for this documentation integration.
