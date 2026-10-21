# k3s

[中文](README.zh-CN.md).

## What it does

Validate a Kubernetes manifest using the original K3s v1.37.1+k3s1 API server and original kubectl in a fresh, private, non-root agentless control plane. Each call proves readiness, zero worker nodes, strict server-side dry-run, post-validation health and cleanup. It does not run Pods, containers, worker nodes or a persistent user cluster.

## Stack

Alibaba generation2 Linuxx86_64/Python3.13, pinned[serverSDK](server-sdk.commit), original81543330byte[official K3s ELF](https://github.com/k3s-io/k3s/releases/download/v1.37.1%2Bk3s1/k3s), publishedSHA25692b94582eb7b34a8cf532e6006842b9ed215a6783cf56a3dd6271fd35243b2c0. [Metadata](upstream.json), source[356c0254](https://github.com/k3s-io/k3s/tree/356c025475bbefaa09cf0d7e48e8e2adbbde57db), original[Apache license](UPSTREAM-LICENSE.md). Build verifies bytes without running the original binary; runtime verifies root-owned original identity. Official[agentless mode](https://docs.k3s.io/advanced#running-agentless-servers-experimental) is a control-plane slice, not workload execution.

## Problem solved

Test real Kubernetes schema/admission behavior before deploying to a user cluster. No caller kubeconfig, cluster endpoint or external account is accepted. A syntax parser alone cannot establish server-side validation; a binary version cannot establish cluster behavior. Valid/invalid results require an actual original private API and post-operation checks.

## Quick start (CLI)

The `abx run` surface uses the verified native0.4.1 entry here. Configure your Express account. Publish exact source first, replace `<published-commit>` with its public40character revision, `<run>` with a unique run and IDs with resources owned by that run. Rename the prepared manifest to avoid replacing any existing template.

```bash
python scripts/prepare_steps.py k3s --output /tmp/k3s-steps-<run> \
  --source-commit <published-commit> --asset-transport parallel
python - <<'CONFIG'
from pathlib import Path
import yaml
p = Path("/tmp/k3s-steps-<run>/template.yaml")
v = yaml.safe_load(p.read_text())
v["name"] = "k3s-<run>"
p.write_text(yaml.safe_dump(v, sort_keys=False))
CONFIG
abx --native template deploy /tmp/k3s-steps-<run> --build steps -y
abx --native create --template <owned-template-id> -y
abx --native run <owned-sandbox-id> k3s_version
abx --native run <owned-sandbox-id> k3s_native_check
abx --native run <owned-sandbox-id> validate_manifest --json-args '{"manifest_yaml":"apiVersion: v1\nkind: Namespace\nmetadata:\n  name: abx-example\n","command_timeout":180}'
abx --native kill <owned-sandbox-id> -y
abx --native template delete <owned-template-id> -y
```

The original Namespace is returned as a dry-run object, never persisted. Template/READY creation does not mean a Kubernetes worker exists. Syntax/source-reviewed examples become provider acceptance only with matching current receipts. The canonical actual original validation uses:

```bash
ABX='abx --native' python scripts/run_steps_e2e.py k3s \
  --sandbox-create sdk --http --asset-transport oss
```

The[pinned optional cache dependencies](../scripts/requirements-steps-cache.txt) enable a temporary private same-account OSS transport with original hash/ACL/independent deletion checks. Generic300MiB archive and15000wire-byte bounds stay unchanged. Native steps need no local Docker; actual Docker-image acceptance is separate.

## Quick start (Python SDK)

Install the[paired agent-sandbox-client](../docs/python-client-installation.md). This keyless program needs only your configured Express account. The standard Express9000server has no command-server Bearer by default; sandbox access credentials are not that Bearer. Use a token only for a process explicitly started with it. The following is syntax checked; cloud acceptance is recorded below.

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox
from agent_sandbox.models.errors import SandboxNotFoundError

async def main():
    sb = await Sandbox.create(template="<owned-template-id>", timeout=900)
    sid = sb.id
    server = sb.server_at(9000, timeout=330)
    try:
        print(await sb.run("k3s_version"))
        result = await server.commands.run("validate_manifest",
            manifest_yaml="apiVersion: v1\nkind: Namespace\nmetadata:\n  name: abx-example\n",
            command_timeout=180, timeout=300)
        assert result["valid"] and result["worker_nodes"] == 0
        assert result["post_api_ready"] and result["probe_not_persisted"]
        assert result["api_server_stopped"] and result["private_state_removed"]
        assert result["node_state_restored"]
        print(result["object"]["kind"])
    finally:
        try:
            await server.aclose()
        finally:
            try:
                await sb.kill()
            finally:
                await sb.close()
    try:
        await Sandbox.get_info_by_id(sid)
    except SandboxNotFoundError:
        pass
    else:
        raise RuntimeError("owned sandbox cleanup is not verified")

asyncio.run(main())
```

Only delete your own sandbox/template. Reconcile ambiguous creates through unique metadata/private intent rather than treating a lost response as cancellation. Create-time environment does not reconfigure prewarmed processes; see[runtime environment](../docs/runtime-environment.md). Optional separately authenticated processes can use SDK start_server9010/PTY9011; their configuration/authentication is distinct from the internal private Kubernetes API.

## Quick start (HTTP POST)

Use the forwarded command-server URL for the owned sandbox. Add `Authorization: Bearer $COMMAND_SERVER_TOKEN` only when that process was started with that independent token.

```bash
curl --fail-with-body -X POST "$K3S_COMMAND_SERVER_URL/commands/validate_manifest" \
  -H 'Content-Type: application/json' \
  --data '{"manifest_yaml":"apiVersion: v1\nkind: Service\nmetadata:\n  name: abx-invalid\nspec:\n  ports: invalid-type\n","command_timeout":180}'
```

A real schema rejection returns HTTP200 with `{"result":{"valid":false,"object":null,"validation_error":"...",...}}` only if original API health/nonpersistence/cleanup still pass. Infrastructure/startup/unclassified native/deadline/cleanup failures are500, never valid:false success. Unknown/type-invalid arguments400; semantic bounds400/500, authentication401 and unknown commands404. `/health`, `/commands`, shell/files share command-server authentication. HTTP disconnect does not cancel the remote operation; its own deadline remains active.

## Command reference

| Command | Parameters/defaults | Result/side effects |
| --- | --- | --- |
| k3s_version | none | Original hash identity and actual version text; no server |
| k3s_native_check | none | Original server help; original_native/agentless_flag_in_help/private_data/private_kubeconfig/explicit_port booleans |
| k3s_setup_check | none | mode/installed/pinned_version/runtime_uid/worker_nodes_supported:false/pods_supported:false/persistent_cluster:false/node_state_empty |
| validate_manifest | manifest_yaml:string required; command_timeout:int180 | Fresh original agentless server, strict dry-run and cleanup |

manifest_yaml:nonblank1..32768UTF8bytes/noNUL; YAML or JSON accepted by original kubectl. command_timeout:integer30..300seconds; booleans refused. No arbitrary flags, external cluster URLs, kubeconfigs, privileged mode, file paths or shell snippets are accepted. Worker uses original `server --config <private-empty> --disable-agent --data-dir <private> --write-kubeconfig <private> --https-listen-port <owned-port> --bind-address 0.0.0.0 --advertise-address <guest-IPv4>`, with coredns/traefik/servicelb/metrics-server/local-storage disabled. The original `kubectl apply --dry-run=server --validate=strict -f <private-input> -o json` performs validation.

Result:valid:boolean, object:original JSON object or null, validation_error:string, runtime_uid:int, worker_nodes:0, api_ready/post_api_ready/probe_not_persisted/api_server_stopped/private_state_removed/node_state_restored:true, native_version/native_sha256/mode. The probe is a separate fresh original Namespace dry-run followed by original get/NotFound before/after validation. No submitted manifest resource is persisted; private bootstrap cluster state is removed. Server errors are classified conservatively; a transport error cannot masquerade as a manifest rejection.

## Configuration

The pinned original --disable-agent flag is hidden from --help (confirmed in immutable upstream source). native_check therefore reports agentless_flag_in_help:false; actual validate_manifest execution, not help text, proves the agentless mode.

Only optional ABX_SERVER_TOKEN for the command server; no model/key/user kubeconfig setting. Child processes receive minimal private HOME/config/cache/TMP plus unique ownership markers, without cloud/model/K3S/KUBECONFIG credentials from the operator. Explicit private native config prevents global K3s config/drop-in inheritance. Certificates, kubeconfig, SQLite data and raw logs stay private and are deleted.

Root build prepares `/etc/rancher/node` as an empty user-owned0700directory. Runtime uses an inode lock across server processes and refuses any pre-existing state unchanged. After an owned run it removes only a matching newly created regular UID-owned33byte native password and confirms an empty directory; foreign files/symlinks/changed identity are preserved and cause failure. Runtime does not invoke SDK user=root; that selector is tracked in[SDKIssue83](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues/83).

Original server and inner kubectl RPC use separate ownership markers; the outer deadline still covers both. Each RPC stdout/stderr is bounded256KiB; native server logs bounded2MiB/stream with only safe diagnostic marker booleans returned on failure. One control plane per sandbox at a time. command_timeout includes startup/validation; allow up to90additional seconds for confirmed cleanup and set client timeout>=command_timeout+120seconds. Caller files, unrelated processes and pre-existing node state are never deleted.

## Resources

Linuxx86_64/nonroot user,2vCPU/4096MB, public command port9000, rootfs build budget8GiB. The temporary TLS API listens on an ephemeral guest port with private generated credentials; it is not a published reusable cluster endpoint. No worker/kubelet/containerd/Pod/Docker/KVM/GPU/persistent-cluster support is asserted. PeakRSS, concurrency throughput, alternate architectures and other providers remain unverified; every validation incurs control-plane startup cost.

## Verified

No provider has a passing run recorded for this template.

Current1.0.0 implementation/local authored-worker checks are in progress; original source-template native Express SDK/fullHTTP/image/cleanup/latestCI/review/merge pending. No original K3s program was executed on the operator. Unit fixtures do not certify Kubernetes. [Executed checks](../.agents/evidence/verify/2026-10-21-k3s-agentless-validation.md).

## Secondary development

```bash
python -m pytest -q k3s/test_runtime.py k3s/test_controller.py k3s/test_install.py
python scripts/check_template.py k3s --strict
python scripts/check_docs.py
```

Publish COPY/helper changes before immutable source preparation, keep all current hashes/receipts and root/nonroot boundaries. Actual runtime acceptance requires original valid Namespace and invalid Service through SDK/HTTP, native post-health/nodecount0/NotFound and independent cleanup. Local socket-connect success is not kernel listener ownership or API readiness; cleanup verifies `/proc` listener absence and identity-pinned process termination. Never infer worker/Pod execution from a healthy agentless API.

## Contributing

Follow[CONTRIBUTING](../CONTRIBUTING.md),[project standards](../docs/project-standards.md),[documentation standard](../docs/documentation-standards.md) and[specification](../docs/template-spec.md). Keep standalone source, bilingual14sections/design/catalog and indexed provenance/evidence aligned; preserve failures and merged history. Current-head CI/review and normal pinned merge are required.

## Issues

[Issue42](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/42),[templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues),[SDK](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues),[CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues),[upstream K3s](https://github.com/k3s-io/k3s/issues). Never attach private cluster credentials, URLs or raw logs.

## License

Authored template and original K3s source are Apache-2.0; original[license](UPSTREAM-LICENSE.md) is retained and installed beside the unchanged original ELF. Bundled components retain their upstream notices/licenses. No original binary is committed and no vendor/provider endorsement is asserted.
