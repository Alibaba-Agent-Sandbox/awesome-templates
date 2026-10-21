# k3s

## Purpose
Real Kubernetes schema/admission validation in disposable owned sandboxes, using unchanged original K3s/kubectl rather than a YAML parser/version wrapper.

## Capabilities
Original non-root agentless control plane with private config/data/TLS/kubeconfig, API readiness and nodecount0, strict server-side manifest dry-run, original fresh Namespace nonpersistence checks, post-health and owned cleanup. No container runtime/worker/Pod/persistent cluster, external kubeconfig or model needed.

## Exposed API
k3s_version, k3s_native_check and k3s_setup_check are readonly diagnostics. validate_manifest(manifest_yaml:str,command_timeout:int=180) accepts1..32768UTF8bytes/noNUL and30..300integerseconds. Returns valid/object/validation_error plus nonroot/nodecount0/readiness/NotFound/serverstatecleanup and native identity. Original server --config private-empty --disable-agent --data-dir/--write-kubeconfig private --https-listen-port ephemeral --bind-address0.0.0.0 --advertise-address nonloopback guestIPv4; disable coredns/traefik/servicelb/metrics-server/local-storage. Original kubectl apply --dry-run=server --validate=strict -f private -ojson. No arbitrary extra argv/URL/file path accepted. Infrastructure/unclassified/cleanup error raises; never returns a validation success.

## How to build
[Dockerfile](../../k3s/Dockerfile) follows Alibaba/noCMD/nonroot9000/generation2. Original v1.37.1+k3s1 ELF81543330bytes/SHA25692b94582eb7b34a8cf532e6006842b9ed215a6783cf56a3dd6271fd35243b2c0 with official release digest, source356c025475bbefaa09cf0d7e48e8e2adbbde57db and original Apache license retained. Root installer verifies bytes and prepares an empty user-owned0700/etc/rancher/node without deleting foreign state. Pinned serverSDK34e7e011c5569f77b7f605e65313be7498f6cf02 and rootfs<=8GiB. Generic same-account temporary cache and15000wire/300MiB limits unchanged. Publish COPY/helper source before immutable preparation.

## Express feasibility
Feasible: slice.

Limiting factor: worker-node/container-runtime nesting is not qualified; original agentless control-plane/API validation must be actually proven on Express before provider qualification.

2vCPU/4096MB/Linuxx64/nonroot; no Docker/KVM/GPU requirement asserted for the slice. Root runtime selection is not used: [SDKIssue83](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues/83) currently ignores commands.run(user=root), so required directory preparation happens during root image/steps build. Usernamespaces or version output alone do not establish a worker cluster.

## Risks
Private empty native config prevents global join/config inheritance; minimal childenv excludes operator/cloud/model/cluster credentials. No user cluster accepted. Global node-directory inode lock, pre-existing-state refusal, identity/shape/UID/timestamp checked password removal and independent absence. Outer worker plus separately marked innerRPC covers foreground/detached native descendants under deadline; native logs bounded2MiB/stream andRPC output256KiB/stream. Native process termination and kernel/proc listener absence, private-state deletion and restored node directory required even after failure. Caller files and unrelated processes preserved. Same OS user is not a multi-tenant isolation boundary.

## Test plan
Authored fixed local worker/archive/controller tests prove API bounds/config/locking/foreign-state/timeout/infra-error and cleanup controls, not Kubernetes. Original native only in an owned cloud target. Canonical native steps/actualSDKcreate/CLI+SDKhelp/version then fullHTTP25/0/0 must actually validate fresh Namespace and bad Service, post-health/nodecount0/original probeNotFound and independent sandbox/template/cache absence. Real image/nonroot/pins/rootfs CI separate. Source/local SKIPs remain explicit; no model/task/other-provider/full cluster claim. Final strict/spec/docs/latestCI/review/normalmerge required.
