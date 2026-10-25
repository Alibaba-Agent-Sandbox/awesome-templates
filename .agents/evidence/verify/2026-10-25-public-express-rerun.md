# Public Express developer rerun

Date: 2026-10-25
Result: PARTIAL — two managed public npm journeys pass; source-image and default source-preparation matrix remains pending.

## Inputs and installation

Read the official public start page, installer and Registry catalog over HTTPS. The catalog has exactly 50 entries: 46 source recipes and four provider-managed identities. Only base/code-interpreter-v1 are Express-managed; desktop is E2B-managed and opensandbox-code-interpreter is OpenSandbox-managed. Cross-provider native identity rejection is not a runtime pass.

Fresh website standalone CLI 0.5.1 installation/version/checksum/provider help passed, but actual base and code-interpreter-v1 launch failed with E4001 before creation. This is preserved as FAIL, separately from npm success. The [CLI fix PR158](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/pull/158) merged as `52be0ac9c7a4fec63b2da193fbd60074e2cae5c4`; actual candidate SEA managed journeys passed, but no new public binary is implied by the merge.

Fresh official npm CLI 0.5.1 installed with an empty cache and separate empty user/global configuration; official PyPI client/server 0.4.0a1 installed in a fresh Python 3.13 environment, followed by pip check. Controller dependencies installed using the repository hash lock. The artifact checker also passes the untouched npm install. Upstream crane 0.22.1 archive/sidecar and executable SHA-256 were verified; ACR temporary authorization token retrieval succeeded without printing values or creating resources.

## Managed real executions

The initial developer journey and the updated canonical `verify_managed_templates.py base code-interpreter-v1 --cli abx` both passed actual public catalog launch, CLI output 42, Python shell/runtime inventory, non-root user, file write/read/delete, CLI deletion and independent get-info absence. The interpreter image imported numpy/pandas/matplotlib and computed dataframe sum 42.

Canonical immutable receipts:

- [base](../../../docs/managed/evidence/public-npm-base-2026-10-25T115215Z.json)
- [code-interpreter-v1](../../../docs/managed/evidence/public-npm-code-interpreter-v1-2026-10-25T115223Z.json)

The receipts retain actual versions and package inventory. No persistent interpreter-session acceptance is claimed. Foreign desktop/OpenSandbox managed names on Express returned E8002 provider-mismatch before creation; no identity substitution was attempted.

## Source prerequisite experiment

The documented default public python-hello source launch was actually invoked with the fresh public npm install. This host has no Docker executable/daemon. It returned generic E8002 and retained one no-ID local build intent before a build started. There were no push/template/sandbox intents. This failed developer journey remains FAIL; [Issue160](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues/160) owns the actionable-error/false-intent correction. No source build or cloud source pass is inferred.

The prepared-image path is also separate: its maintained consumer refuses incomplete/failed export workflows, unverified images and public exports conflating verifier and source revisions. No current 46-entry Express result is claimed yet. The new public export/source controller workflow is being independently run; source inputs and verifier code remain explicitly distinguished.

## Checks and cleanup

Focused archive/managed regressions: 19 PASS, including separate public/verifier identities, official package source checks, known-ID cleanup after connect failure and CLI kill failure. Earlier combined existing runner/controller regressions: 52 PASS. These are local tooling checks, not cloud acceptance.

All known managed sandboxes from these runs were deleted and independently confirmed absent. Original public-binary failures created no resources. The original absent-Docker local intent remains historical evidence; no global or shared resource deletion is used. Source-image execution, its registry/template/sandbox cleanup, and final published-binary retest remain pending.

## Prepared-image experiment and cleanup follow-up

The first private python-hello attempt completed archive validation, private ACR transfer and template registration, then the runtime session ended before application acceptance. This is an interrupted experiment, not proof of a product failure. The exact owned template/sandbox inventory and both registry tags/repository were recovered and independently confirmed absent.

A second attempt registered the image without a prestarted application and used current `template launch` to start the original declared service, retaining its startup/services/env in a private manifest with the owned ID. Launch and the first CLI hello returned successfully. The direct host HTTP probe then raised ConnectError; that attempt remains FAIL. A separate fresh owned base sandbox proved the same provider-resolved endpoint/headers fail with `trust_env=False` and return HTTP 200 with normal environment proxy settings. Its sandbox was deleted and typed get-info confirmed absence. The consumer now respects environment proxies without disabling TLS verification.

The failed attempt initially could not confirm sandbox cleanup; a separate recovery subsequently confirmed typed SDK NotFound for its exact owned sandbox. Its template and private ACR repository/tags were already independently absent. Raw failed results are preserved separately from the recovery; no runtime success is inferred from cleanup.

The one-time complete-snapshot reconciliation needed by the old export's incorrect source label is frozen with the experiment artifacts. It is deliberately removed from maintained scripts, along with its selectors; new exports must contain the correct explicit public/verifier identities. The old metadata's server source field is a declared recipe pin, not proof of the actual injected runtime source. Its observed runtime version is 0.3.0 and must not be relabelled as the host's installed 0.4.0a1 package.

Maintained image acceptance now uses only `ProviderSandbox`, `application_client`, current CLI/host HTTP, and the shared launch startup. It no longer starts a sibling application on port 9010 or selects between SDK/CLI creation modes. Focused archive/managed/current-startup/controller regressions: 81 PASS. `scripts/test_spec_tools.py`: 58 PASS; `scripts/check_template.py --all`: 46 conformant/0 failures; `scripts/check_docs.py`: 222 documents/0 link failures. These are tooling checks, not a full prepared-image matrix pass.

The final matrix requires the latest paired public server/client version and freshly built images, then a fresh public CLI install. Old image experiments are stopped rather than extended into a stale 45-entry acceptance run.

## Current-main and published a2 tooling integration

Normal merge of current main ecaacebd1582c033049ff9f32038e0249f80f82a retained both the public Express and controller-authentication records. The Chinese public launch guide uses only ABX_SERVER_TOKEN; application and provider gateway credentials remain separate. No old token aliases were restored.

Current tooling validation with the actual official PyPI client/server 0.4.0a2: archive, current managed lifecycle, shared HTTP controllers and public launch regressions 68 PASS; provider missing-key-before-engine and unsupported-interpreter-before-transport boundaries 2 PASS. CI host dependencies now install public a2 and provider fixture 48f09103380657ad7e5ea97422e50156cb01e1dc, rather than incompatible old provider/API snapshots. Document links: 222 documents, zero failures. These are tooling and read-only boundary checks, not a new Express image/source matrix result. Runtime public pins, final image digest gate, archive proof field cleanup and the complete new-runtime matrix belong to dependent PR222.
