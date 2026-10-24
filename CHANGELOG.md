# Changelog

## Unreleased

- Publish the complete 46-source × Express/OpenSandbox launch evidence with exact public-package inputs, separate remote Git checks and cleanup results. Keep managed entries and real-model/native-interface claims separately scoped.
- Align source-template quick starts with running application connections, provider selection, gateway authentication and owned cleanup in both languages.
- Recommend public CLI 0.4.17 and document its application HTTP timeout for long Qwen tasks; use the public Python `ProviderSandbox` entry. Existing cloud receipts retain CLI 0.4.16 and their original inputs.

- Change the managed `opensandbox-code-interpreter` default from the unimplemented
  `native-interpreter` workflow to the existing `exec` create/process path. Consumers
  explicitly selecting the old workflow name must select `exec` for project-managed
  execution. Native interpreter sessions remain available through the upstream SDK
  with an explicit service entrypoint; this does not add a unified interpreter adapter.
- Simplify the four managed templates' English/Chinese usage guides, use the public
  `ProviderSandbox` entry, and separate current behavior from dated evidence.

- Validate managed service/operation references and exec startup commands with the same semantics as source templates; reject service bindings on other workflow kinds and commandless managed exec startup.
- Remove the unused legacy local runtime profile and document only the strict current managed catalog fields.
- Align13 template server fallbacks and the skeleton with the CI source pin; reject default/fallback drift and preserve old receipts as history. Changed template contracts receive patch versions and require new image/workflow acceptance.
- Pin Qwen Node24.16.0 with official x64/arm64 SHA256 verification instead of a moving setup script.

- Replace template specification 2/3 with specification4 and explicit provided services, workflows and a default workflow. Retired compatibility and handwritten verification fields are rejected.
- Separate application deployment topology from sandbox invocation paths, and managed inputs from source builds. Preserve application hooks and durable-state semantics.
- Bind full manifest identities without qualification exclusions. Historical receipts remain scoped reports; only independently trusted workflow evidence can certify a current path.
- Remove interpreter shell-fallback claims from managed exec verification. Keep Dockerfile/base/entrypoint inputs explicit.
