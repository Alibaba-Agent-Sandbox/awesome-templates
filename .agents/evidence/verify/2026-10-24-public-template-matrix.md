# All source templates through the public CLI

Result: PASS — 46 templates × 2 platforms, 92 application and cleanup reports.

[Run 40115813586](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/40115813586)
completed successfully, including the plan job and all 92 launch jobs. The
[summary](2026-10-24-public-template-matrix/summary.json) lists each immutable report
and its SHA256; all original report bytes are preserved in this repository.

## Exact inputs and scope

| Input | Version or commit |
| --- | --- |
| Tested templates | `e581d273aa1b7bbc099da8c4c7745c1728230364` |
| CLI from npmjs.org | `@agent-sandbox/cli@0.4.16`; source `413d575a688bd6f870c42c711d11346d176e0f38` |
| Host client and server from PyPI | `0.3.1a5`; source `1b235830bc4a8cbec275b530bf2dc2869e8d0c4b` |
| Local provider checkout | `e18489155697dcf2ee55a47b403396069d6cfa20` |
| OpenSandbox | Disposable Docker-backed 1.1.1, default direct endpoint |
| Express | Real cloud build, registration, create, execution and deletion |

Each fresh runner installed the exact public distributions, checked their versions
and ran `pip check`. The host `python_server` field is not an in-image version
claim. Each template image retains the server source pinned by its own Dockerfile
and optional `server-sdk.commit`; runtime identity compares the manifest and
`commands.py` bytes. No recipe/server pin was changed for this run.

The provider and template inputs here were fixed local checkouts. This proves the
public CLI’s preparation and launch path, not remote Git download or Registry ZIP
installation. The separate [public Git journeys](2026-10-24-public-git-journeys.md)
exercise the published website commands and record their exact provenance limits.
The [public-package pilot](2026-10-24-public-install-pilot-2.md) precedes this run.

The tested commit and merge `ba17fbd32da188a2e4452f5946fa72135fc41c8e` have the
same Git tree `0529cdf8087a4a10ee1cb46eaaa91beb9b898b20`; see the
[readback](2026-10-24-public-template-matrix/tested-merge-tree-identity.json).
Later managed-entry and documentation changes have separate evidence. This
identity statement does not claim that every subsequent main commit has that tree.

## Assertions and limitations

All cases launched their unchanged default source using installed `abx template
launch`, without runner-side Dockerfile preprocessing, an explicit portable profile,
a private bridge address, or guest-side HTTP substitution. Each manifest smoke
command ran independently through CLI, Python application client and host HTTP.
Where the manifest defines `expect`, each consumer checks it. Otherwise the check
establishes a nonempty successful invocation, not complete product correctness;
time-dependent responses are not required to match one another.

Each report also passed wrong-token HTTP 401 rejection, runtime source identity,
SDK process execution and a file write/read/delete round trip. These are keyless
smoke checks. They do not establish real-model tasks, native interpreter, PTY,
interactive desktop or every upstream product feature. OpenSandbox server-proxy
compatibility and managed native interpreter behavior have their own separately
scoped receipts; default direct results do not certify those paths.

## Cleanup and reproduction

Every report independently confirmed sandbox and prepared-artifact absence with
zero cleanup failures, retained artifacts or uncertain intents. Cleanup uses exact
owned journals/tags and does not delete shared image repositories. Each OpenSandbox
job also successfully stopped its disposable backend and image registry. After the
last full-matrix and extra Git/Qwen runs finished, the six task-created
`PUBLIC_LAUNCH_` repository secrets were deleted and their absence read back;
[the receipt](2026-10-24-public-template-matrix/task-secrets-cleanup.json) contains
names only. Existing repository secrets were not changed.

Reproduce using the existing
[public launch testing guide](../../../docs/public-launch-testing.md), selecting
`templates=all`, `provider=both` and the exact input commits above for
`.github/workflows/public-template-launch.yml`. Supply your own provider
configuration and unique task secrets. A local one-case invocation is:

```bash
python scripts/public_launch_e2e.py python-hello --provider alicloud-express --source ./python-hello --output attempt.json
```

Previous failed package-install, proxy and native-fixture attempts remain preserved;
this new run does not rewrite or relabel them. The current template maintenance
status is independent of these dated runtime results.

## Per-template results

| Template | Express | OpenSandbox direct |
| --- | --- | --- |
| agents-cli | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-agents-cli-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-agents-cli-40115813586-1.json) |
| aider | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-aider-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-aider-40115813586-1.json) |
| amp | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-amp-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-amp-40115813586-1.json) |
| apply-patch | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-apply-patch-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-apply-patch-40115813586-1.json) |
| appworld | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-appworld-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-appworld-40115813586-1.json) |
| browser-automation | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-browser-automation-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-browser-automation-40115813586-1.json) |
| browser-use | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-browser-use-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-browser-use-40115813586-1.json) |
| chrome | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-chrome-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-chrome-40115813586-1.json) |
| claude-code | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-claude-code-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-claude-code-40115813586-1.json) |
| cline | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-cline-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-cline-40115813586-1.json) |
| code-server | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-code-server-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-code-server-40115813586-1.json) |
| codex | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-codex-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-codex-40115813586-1.json) |
| codex-agent-api | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-codex-agent-api-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-codex-agent-api-40115813586-1.json) |
| copilot-cli | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-copilot-cli-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-copilot-cli-40115813586-1.json) |
| crush | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-crush-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-crush-40115813586-1.json) |
| cursor-agent | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-cursor-agent-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-cursor-agent-40115813586-1.json) |
| deepagents | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-deepagents-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-deepagents-40115813586-1.json) |
| deepseek-harness | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-deepseek-harness-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-deepseek-harness-40115813586-1.json) |
| dev-services | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-dev-services-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-dev-services-40115813586-1.json) |
| devin | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-devin-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-devin-40115813586-1.json) |
| document-tools | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-document-tools-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-document-tools-40115813586-1.json) |
| droid | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-droid-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-droid-40115813586-1.json) |
| gemini | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-gemini-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-gemini-40115813586-1.json) |
| goose | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-goose-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-goose-40115813586-1.json) |
| grok | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-grok-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-grok-40115813586-1.json) |
| hermes-agent | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-hermes-agent-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-hermes-agent-40115813586-1.json) |
| kimi-code | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-kimi-code-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-kimi-code-40115813586-1.json) |
| media-tools | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-media-tools-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-media-tools-40115813586-1.json) |
| muse | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-muse-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-muse-40115813586-1.json) |
| next-app | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-next-app-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-next-app-40115813586-1.json) |
| node-web | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-node-web-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-node-web-40115813586-1.json) |
| ocr | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-ocr-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-ocr-40115813586-1.json) |
| openclaw | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-openclaw-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-openclaw-40115813586-1.json) |
| opencode | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-opencode-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-opencode-40115813586-1.json) |
| osworld | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-osworld-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-osworld-40115813586-1.json) |
| pi | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-pi-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-pi-40115813586-1.json) |
| polyglot-toolchain | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-polyglot-toolchain-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-polyglot-toolchain-40115813586-1.json) |
| prime-agent | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-prime-agent-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-prime-agent-40115813586-1.json) |
| python-hello | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-python-hello-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-python-hello-40115813586-1.json) |
| qm | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-qm-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-qm-40115813586-1.json) |
| qm-sandbox | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-qm-sandbox-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-qm-sandbox-40115813586-1.json) |
| qoder | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-qoder-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-qoder-40115813586-1.json) |
| qwen-code | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-qwen-code-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-qwen-code-40115813586-1.json) |
| stagehand | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-stagehand-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-stagehand-40115813586-1.json) |
| swe | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-swe-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-swe-40115813586-1.json) |
| tau2-bench | [PASS](2026-10-24-public-template-matrix/public-launch-alicloud-express-tau2-bench-40115813586-1.json) | [PASS](2026-10-24-public-template-matrix/public-launch-opensandbox-tau2-bench-40115813586-1.json) |

## Evidence-only change validation

Independent reconciliation found exactly 46 unique templates on each provider,
92 matching successful jobs/reports, and 438 smoke command invocations across the
three consumers. All receipt JSON parses and the configured-credential value scan
passed without printing secret values. Local current-document link validation
passed (222 documents), as did the six explicitly checked new/updated record and
PR-template documents. The repository’s normal current-head CI and review remain
the merge gates; this record does not substitute the cloud run for those checks.
