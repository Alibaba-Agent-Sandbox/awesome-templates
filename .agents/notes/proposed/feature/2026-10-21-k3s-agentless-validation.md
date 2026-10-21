# Decision: original agentless K3s validation slice

Status: proposed

## Problem
Issue42 asks what actually runs under Express rather than inferring full cluster support from a binary version or missing KVM. Full worker/runtime nesting is not qualified. Earlier unpublished temporary implementation was lost during runtime reset; it is not current evidence.

## Decision
Implement a useful standalone non-root original agentless control-plane slice: a fresh private server, original API readiness/nodecount0, original server-side strict manifest dry-run and post-health, then stop and independently confirm owned state/listener cleanup. No worker/container/Pod execution claim. Root-only build prepares an empty private native node-state directory; runtime never depends on the known SDK user=root defect.

## API Design
k3s_version, k3s_native_check, k3s_setup_check; validate_manifest(manifest_yaml:str,command_timeout:int=180) with1..32768UTF8bytes and30..300integerseconds. No arbitrary argv/cluster URL/kubeconfig. A private empty native config, data, TLS/kubeconfig and disposable Namespace probe isolate each operation. Original validation errors are distinct from infrastructure failures; post-ready/nodecount/probe absence/cleanup mandatory. Global node directory uses inode flock and refuses pre-existing state unchanged.

## Alternatives considered
A version-only wrapper cannot establish Kubernetes behavior. Rootless full worker setup needs additional namespace/cgroup/network capabilities; missing KVM does not by itself disprove other modes. Official --disable-agent is a concrete control-plane-only mode and never proves Pod execution. No caller cluster or external model key is used. SDK commands.run(user=root) currently ignores principal selection (python-sdkIssue83), so required directory preparation belongs to root image/steps build, not a false runtime root call.

## Dependencies
Official v1.37.1+k3s1 source356c025475bbefaa09cf0d7e48e8e2adbbde57db, original ELF81543330bytes/SHA25692b94582eb7b34a8cf532e6006842b9ed215a6783cf56a3dd6271fd35243b2c0, official release digest/checksum and original Apache2.0license preserved. ServerSDK34e7e011c5569f77b7f605e65313be7498f6cf02,2vCPU/4096MB/Linuxx64/nonroot and owned Express. No external account beyond sandbox provider.

## Test Strategy
Authored fixed workers locally cover argument/config isolation, native-shape dry-run controls, infra-error rejection, foreground/inner RPC/outer deadline and cleanup while preserving unrelated processes/foreign files. Original server/CLI only in owned Express after publishing exact source/helper. Native SDKcreate/CLI+SDKdiagnostics/fullHTTP real valid/invalid manifests, original post-health/nodes0/probeNotFound and independently confirmed template/sandbox/cache absence. Separate actual image/rootfs/pinCI and final source audit. Local kernel listener checks use /proc, not TCPaccept that may be intercepted.

## Acceptance criteria
Complete standalone source/bilingual14section docs/design/catalog, local regressions/spec/strict/docs, actual image and canonical current-source steps/SDK/fullHTTP/cleanup, exact-headCI/review/normalmerge. Preserve failures/skips as history. No full cluster/model/other-provider success from this slice.

Second canonical original Express run at source `cca499c217ea8cd5cc4bb1a9cc1843380352d7a0` failed after158.971seconds: fullHTTP14PASS1FAIL0SKIP. Version smoke now matches the original banner; server readiness still fails with RuntimeError and no whitelisted native-log marker. Independent owned VM/template/cache cleanupPASS. [Second failure](../../../evidence/verify/2026-10-21-k3s-second-native-failure.json) is retained separately. Added bounded numeric startup/exit/config/log-byte/OOM counters, with no native log text, to distinguish startup failure, process termination and deadline. Local runtime/controller/installer/asset tests42PASS7.27seconds. The25check native acceptance gate is unchanged; Issue42 remains open and tested_on stays empty.
