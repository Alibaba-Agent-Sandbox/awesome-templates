# code-server

## Purpose

Provide the actual authenticated browser IDE and isolated owned lifecycle for editing sandbox workspaces.

## Capabilities

Upstream standalone code-server4.141.0, command API9000 and password-protected IDE8443; owned configuration/user-data/extensions, caller workspace preserved. No model, display, GPU, Docker or KVM. HTTP auth/workbench and process cleanup are tested separately from WebSocket/terminal interaction.

## Exposed API

code_server_version() -> actual version. code_server_start(password: str="",port: int=8443,cwd: str="",timeout_s: int=60) -> {port,running,auth}; password12..256 UTF-8 bytes or server CODE_SERVER_PASSWORD, valid unreserved port1024..65535, existing WORKSPACE subdir, startup1..120s. code_server_status() -> liveness/port/auth. code_server_stop() -> stopped only after owned worker exit/kernel-listener/private-state cleanup. code_server_self_test() -> CODE_SERVER_OK after real wrong-password, login cookie and authenticated workbench. No logs, cookie or password is returned.

## How to build

[Dockerfile](../../code-server/Dockerfile), official Linux x86_64/aarch64 standalone assets with fixed SHA256/size, retained upstream notices and8GiB visible-rootfs budget using du -sx. Download bound240s. Alibaba base v0.0.49; server e2cb27e fallback/source wheel. generation2 start_cmd `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`, ready_cmd `agent-sandbox-server healthcheck --port 9000`. Final USER user,2vCPU/2048MB,9000/8443; no CMD/ENTRYPOINT.

## Express feasibility

Feasible: yes

Limiting factor: image/rootfs budget and forwarded IDE WebSocket transport. Architecture fits non-root/no-KVM/no-Docker; actual image/cloud/forwarding acceptance remains required. Linux pidfd/process/procfs support is mandatory and fails before launch if unavailable.

## Risks

Private password config0600, directory0700. Cloud/model credentials are not inherited; user extensions/terminal commands are trusted sandbox workloads. Own nonce plus pidfds prevent PID reuse/unrelated-worker signaling; cleanup failure retains authority rather than reporting success. No broad process-name kills. Listening readback uses kernel TCP tables, because the operator environment transparently accepts connections to empty ports. Upstream notices and extension licenses stay intact.

## Test plan

L0 actual code-server version/login/wrong-password/workbench, external UI route, lifecycle persistence and cleanup, caller settings byte/mode preservation and credential-env exclusion. Real readiness deadline, unrelated-listener protection and ownership-error negative controls. L1 actual non-root image/version/self-test and rootfs budget. L2 actual Express steps/deploy READY, CLI+SDK self-tests, complete external HTTP/forwarded8443 and independently confirmed resource absence. WebSocket/terminal needs explicit separate proof. L3 no model; L4 unrun.

Default-domain access is a concrete current operator blocker: a real minimal
HTML control independently confirmed forced attachment and Chromium download,
matching the FC default-domain policy. Full browser IDE acceptance requires a
provider-supported custom preview domain/certificate and a successful exact-hash
browser controller run. Backend HTTP5 success alone is insufficient. The first
control confirmed list absence but used an unavailable extra GET helper; the
second uses the actual get_info_by_id API and independently confirms both absence
paths. Both original point-in-time records remain unchanged.
