# openclaw

## Purpose

Provide an authenticated OpenClaw gateway within a generation-2 Agent Sandbox.
The gateway is a WebSocket runtime, not a one-shot coding command. Its readiness
must return while the process remains alive.

## Capabilities

Start one owned background gateway, report its process status, execute a real
authenticated health RPC, and stop that process group. Standard server shell,
files and ports remain available. The verified runtime slice excludes model
execution, channels, browser/control UI and nested Docker-based agent sandboxing.

## Exposed API

[Command reference](../../openclaw/README.md#command-reference) is the canonical
parameter/default/type/return contract, mirrored in the Chinese README.
`gateway_start(port:int=18789, bind:str="loopback", command_timeout:int=60)` runs
`openclaw gateway run --allow-unconfigured --bind <bind> --auth token --port <port>`.
`gateway_health(command_timeout:int=20)` runs `openclaw gateway health --json --timeout
<milliseconds>` with the same isolated configuration and environment. Only its
JSON `ok:true` counts as health. `gateway_status()` reports `{running,owned,url}`
from a Popen handle. `gateway_stop(command_timeout:int=10)` terminates and reaps the owned
process group. All parameters are optional; timeouts must be 1..120 seconds.
`gateway(action:str="start", port:int=18789, bind:str="loopback", command_timeout:int=60)`
preserves the old command name with an explicit bounded action enum.

## How to build

Template2.0.1 explicitly owns /home/user/app as user:user before runtime USER. This repairs actual non-root workspace mkdir/write failures. Earlier provider receipts retain their original source-version scope; this changed profile requires new acceptance.

[Dockerfile](../../openclaw/Dockerfile) uses the Alibaba FC base, installs pinned
Node 24.16.0 from the official architecture-specific tarball with embedded
SHA256 verification (x64/arm64), and OpenClaw 2026.10.4, cleans npm cache, then installs a deployment
wheel or the server archive pinned to python-sdk commit
`35da216a300f1e2e84254a1cf4b4a7ea98681505`. Workdir is `/home/user/app`; runtime
is `USER user`; no CMD or ENTRYPOINT. The package metadata requires Node
`>=24.16.0 <25 || >=26.1.0`; Node 20/22 from older images is insufficient.
The platform starts `agent-sandbox-server serve --port 9000 --commands
/home/user/app/commands.py`, probes `agent-sandbox-server healthcheck --port 9000`,
and uses generation 2. The Docker install/build has not been validated here.

## Express feasibility

Feasible: slice

Limiting factor: nested Docker-based agent sandboxing is unavailable on Express.

The gateway itself uses non-root user, no privileged operations, no KVM or Docker.
2 vCPU and 4096MB are requested. Outbound access is needed for install and optional
models. Only the gateway lifecycle is currently accepted locally; image size,
Express readiness and provider port forwarding remain unverified.

## Risks

Linux health-RPC subprocesses use concurrent pipe draining and waitid(WNOWAIT), then clean their owned group before reaping on success/error/timeout. The separate long-lived gateway group is unaffected. A process deliberately escaping with setsid is outside that group.

Token auth is mandatory for start; token values travel in child environment,
with an environment reference in a temporary private config. No token parameter,
stdout or stderr is returned. Loopback is the default; lan requires conscious
port exposure. Child stdout/stderr are discarded to prevent leaking credentials.
Configuration and state live in a private temporary directory; stop removes them.
No PID file is used, no --force port reclamation occurs, and stop cannot signal
an unrelated process named by stale state. Concurrent lifecycle calls serialize
through one lock. Linux waitid(WNOWAIT) status observation preserves even an unexpectedly exited
leader. Shutdown keeps the leader unreaped until the final group
KILL, so TERM-ignoring descendants cannot survive and a recycled PGID cannot be
targeted. Abrupt server death loses ownership; restart will not adopt or
kill the old process. Destroy the sandbox to clean such an orphan. Ordinary exit
also attempts bounded atexit cleanup. This is intentionally an ephemeral runtime.

## Test plan

- L0: `python3 scripts/check_template.py openclaw`,
  `python3 -m pytest openclaw/test_commands.py`, and local server HTTP suite.
  Verify invalid type is HTTP400 and explicit invalid action fails HTTP500;
  never accept arbitrary HTTP500 as success. With a synthetic gateway token,
  require real gateway authenticated readiness/health, still-running status,
  stopped status and failed health after cleanup. Without the token report SKIP.
- L1: build Docker image and verify Node24.16.0/OpenClaw2026.10.4/non-root startup.
  Not executed without Docker; do not call local npm installation an image pass.
- L2: `python3 scripts/express_e2e.py openclaw`; smoke `gateway_status` must return
  `{running:false,owned:false,url:null}`. Then perform authenticated gateway
  lifecycle with an injected random token. No provider pass has been recorded.
- L3: no model command in this patch. A later coding acceptance must configure
  an upstream-supported model, perform real work and assert `ABX_E2E_OK`.
  Gateway health does not satisfy this tier.
- L4: not attempted; no additional provider is claimed.

Sources: [official gateway CLI](https://docs.openclaw.ai/cli/gateway), installed
`openclaw@2026.10.4 --version` and `gateway health --help`, plus npm package engines.
Work tracks [Issue #20](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/20).

## Version2.1explicit proxy profile

Actual2.0.1 native authenticated gateway start/RPC and externally forwarded healthz pass, but forwarded readyz returns403 under the pinned upstream's proxy-attribution policy. Add only explicit operator OPENCLAW_TRUSTED_PROXIES IPs/CIDRs to the owned private config. Refuse invalid/empty/whole-Internet/multicast entries; cap16addresses/2048bytes and canonicalize duplicates. Never infer trust from X-Forwarded-For or introduce universal trust. Defaults and token authentication remain. Current2.1native steps and exact CI image now pass actual SDK auth lifecycle, external healthz/readyz and independent owned process/state/sandbox/template/registry cleanup; see the [final record](../../.agents/evidence/verify/2026-10-20-openclaw-native-sdk-final.md). Old2.0.1receipts stay historical.

The borrowed-sandbox SDK controller owns an ephemeral nonce probe on9012, then explicitly configures its own9010server with that observed kernel peer's exact address for testing. Native gateway runs on18789 with token auth; SDK lifecycle, externally forwarded liveness/readiness and independent listener/state cleanup are required. The probe shuts itself down naturally; the caller retains sandbox ownership. No agent/model/channel claim is added. Source/controller tests and actual1:1 image/step proof are separate.
