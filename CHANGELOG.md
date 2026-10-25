# Changelog

## Unreleased

- Use published server 0.4.0a3 in all declared source recipes with minimal template patches. Correct stale Git/wheel runtime documentation, remove the four retired project command aliases, and update QM consumers to the reviewed current immutable Node SDK source. Preserve historical evidence and require fresh current-input image/provider acceptance. / 所有源码构建统一已发布 a3 服务端并最小增加模板版本，清理四个旧命令转发及过时运行时说明；QM 使用已审核的当前 Node SDK 源码，重新验证真实平台。

- Install published server 0.4.0a2 directly in all source recipes and increment their patch versions. Remove pre-release archive/wheel fallbacks and duplicate historical cloud runners; retain keyless image gates and full current public-launch acceptance with actual guest package readback. Selected image batches always rerun.

- Current Express acceptance uses public managed catalog launch and the shared whole-template startup for prepared images; remove duplicate SDK creation and test-only sibling service paths. Preserve original failures, runtime/package provenance and exact owned cleanup separately. / 极速版验证统一使用当前模板启动与公共 SDK，移除重复创建分支和测试专用第二服务；分别保留失败、来源与资源清理证据。
- Remove retired E2E application-token aliases from current template controllers and use only ABX_SERVER_TOKEN, keeping provider gateway headers separate. Use the current OpenSandbox credential name in managed examples.
- Fix Chrome 1.0.6 CDP and noVNC connections through provider endpoints with a path prefix or fixed query. Preserve existing gateway and application authentication.

- Introduce template specification 5: one startup command and all provided services, with no workflow selector. Migrate all source manifests and managed references, retain every runtime command and recipe, and update launch examples and the public acceptance harness.
- Require an explicit migration from specification 4 by deleting `workflow_contract_version`, `default_workflow` and `workflows`. A compatible CLI/SDK build is required; earlier cloud receipts remain historical and do not certify specification 5.

### Previous delivery history

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
