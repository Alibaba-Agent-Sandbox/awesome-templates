# Public Git installation and template journeys

Result: PASS for both platforms, with the provenance limits below.

The actual published Registry pages used:

- [Express python-hello](https://registry.agent-sandbox.cn/templates/python-hello/launch/alicloud-express/): `abx --provider alicloud-express template launch alibaba-agent-sandbox/awesome-templates//python-hello --workflow application`.
- [OpenSandbox python-hello](https://registry.agent-sandbox.cn/templates/python-hello/launch/opensandbox/): install `alibaba-agent-sandbox/awesome-providers//opensandbox --allow-unpinned`, then the same template launch with `--provider opensandbox`.

The host runner used published CLI 0.4.16 and paired Python packages 0.3.1a5.
Those installed-package fields do not describe the template image server SDK, whose
fixed source remains defined by the template recipe. The runtime identity check
compares commands.py bytes. The test retained the
existing application token/configuration and independent owned-resource cleanup.
Noninteractive `--yes`, a unique owned alias and explicit test timeouts were added.
CLI provider installation fetches public Git; this is not a Registry ZIP download.

## Actual website command journey

[Run 40118565897](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/40118565897)
passed both jobs. The [test branch commit](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/commit/59b3a866c2f9afd38b54d56652d16c89b2b43309)
changes only the existing workflow's provider install source and template source.
Both are remote Git sources, rather than the full matrix's local checkouts.

The original reports are preserved in [unfixed-git](2026-10-24-public-git-journeys/unfixed-git/).
Their `installed_packages.provider_source_ref` is the checkout fixture reference,
not proof of the remotely installed provider revision. The actual resolved template
and provider commits were not recorded in this run. Template launch returned the
recorded source/manifest digests, but the released CLI does not expose the resolved
commit for an unfixed template download. These unknown commits are not reconstructed
from a later query of main.

## Reproduction with explicit template commit and actual provider receipt

[Run 40119284307](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/40119284307)
also passed both jobs. Its [test branch commit](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/commit/d1e33070351e026e7cba797210defd95d2332d9d)
requests the remote template at exact commit
`ba17fbd32da188a2e4452f5946fa72135fc41c8e`, verifies runtime manifest/command identity,
and records the returned source digest. Source preparation is provider-specific;
its digest is not represented as a Git commit or Git tree hash.

OpenSandbox still installs via the website's unfixed Git command. Its actual
`.abx-install.json` receipt records commit
`998a9d6a438f5c9b1f149ace26608b4132222b1c` and tree SHA256
`79f089c85ca66538208bd5916a9322f4a6474b4a8eda0e15f5a8627c726695bb`.
Only these allowlisted provenance fields are copied into the new report. Express
uses the provider built into the installed CLI/Python packages. The separate fixture
reference is explicitly labeled as such. See [fixed-git reports](2026-10-24-public-git-journeys/fixed-git/).

In all four cases, CLI/Python/host-HTTP smoke calls, wrong-token rejection, runtime
source identity, SDK process/file operations and cleanup passed. Sandbox and prepared
artifact absence were independently confirmed, with zero retained artifacts, uncertain
intents or cleanup failures. OpenSandbox used its default direct endpoint on the
isolated Docker backend. No model, native interpreter, PTY or desktop acceptance is
inferred from these two-template-source journeys.
