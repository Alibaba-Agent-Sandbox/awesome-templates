# node-web

## Purpose

Give agents a generic Node HTTP application runtime for Express/Fastify-style projects, with reliable startup and cleanup. This is the existing P1 / wave 1 template tracked in awesome-templates#29; it does not scaffold Next/Vite or install unrelated CLIs.

## Capabilities

Run one Node HTTP service, inspect process and HTTP health, send bounded loopback GETs, collect continuously drained rotating stdout/stderr, run real npm builds and stop npm plus child processes. Built-in shell/files/code/ports APIs support uploading a project, fetching build artifacts and obtaining its gateway preview URL. `index.js` is a dependency-free working HTTP example.

## Exposed API

All parameters are optional; exact ranges and responses are in [the command reference](../../node-web/README.md#command-reference).

| Name | Parameters and defaults | Return and upstream call |
|---|---|---|
| serve | entry: str=index.js; port: int=3000; cwd: str=empty; ready_path: str=/; timeout_s: int=20 | Running metadata after HTTP readiness; argv `node <resolved-entry>` |
| start | port: int=3000; cwd: str=empty; ready_path: str=/; timeout_s: int=20 | Running metadata; argv `npm start` |
| dev | port: int=3000; cwd: str=empty; ready_path: str=/; timeout_s: int=20 | Running metadata; argv `npm run dev` |
| status | none | Process state plus actual HTTP readiness |
| stop | none | Stopped metadata after terminating owned process group |
| logs | max_bytes: int=16384 | Bounded latest merged stdout/stderr |
| request | path: str=/; timeout_s: int=5 | Real HTTP status/body/truncation; loopback only |
| build | cwd: str=empty; timeout_s: int=120 | argv `npm run build`; exit code, bounded output, truncation; failures raise |
| smoke | none | Start bundled service, assert status 200 and exact body, always stop; string `node-web ready` |

## How to build

[Dockerfile](../../node-web/Dockerfile) uses `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>` (default resolved tag v0.0.49), with base-provided Node 20/Python 3.13. Server archive is pinned to full commit `35da216a300f1e2e84254a1cf4b4a7ea98681505`. A wheel injected by the deploy CLI wins. No additional pip/npm dependencies, so no npm lockfile is necessary for the built-in sample. User applications must supply their own lockfile.

Build context contains Dockerfile, commands.py, index.js and optionally an injected wheel. Runtime is non-root user in `/home/user/app`. Generation 2 starts `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py` and probes `agent-sandbox-server healthcheck --port 9000`. No image CMD/ENTRYPOINT.

## Express feasibility

Feasible: yes

Limiting factor: none

The full service lifecycle fits non-root user, 2 vCPU/2048 MB, no KVM/Docker/extra capabilities and about 10 GB rootfs. Custom application dependencies remain within that resource budget. The application's own listener must bind 0.0.0.0 and honor PORT for gateway exposure. Local L0 does not establish provider connectivity.

## Risks

The old implementation never consumed child PIPE output and ran npm start/dev synchronously. A continuous binary drainer now consumes both streams into two 1 MiB rotating files. A 4 MiB-before-listen regression respects Node backpressure and fails if the drainer stops working. Returned logs are capped at 128 KiB; HTTP bodies at 64 KiB.

Service launch reserves a free port, rejects an already managed live process, checks HTTP 2xx/3xx and child liveness, and tears down the process group on failure. A short reserve/release race remains possible against unrelated processes in the same sandbox. Process ownership is in memory and not durable across command-server restarts. `stop` handles npm descendants in the same process group; explicitly detached grandchildren are outside its guarantee. Sandbox destruction is the final cleanup boundary.

Build output uses a temporary file to avoid pipe deadlock/unbounded returned output, but can consume disk until completion; build deadlines are at most 600 seconds. This executes user code with sandbox-user privileges and does not enforce a separate project filesystem boundary. request permits only local paths, does not follow redirects and never accepts arbitrary hosts. No model/provider secrets are needed. User applications must redact their own logs before publication. No credentials are embedded in metadata, image or evidence.

## Test plan

`check()` emits bracketed `[PASS]`/`[FAIL]` labels consumed by the strict external
image acceptance counter. The prior script had a valid entrypoint and exited0
but emitted unbracketed `PASS`; the counter recognized0 assertions and correctly
refused acceptance. Preserve that historical rejected result. The focused
`test_http_output.py` launches the real SDK server and Node/npm lifecycle suite,
requires all60 countable assertions with no failure/skip, and exercises a real
HTTP503 failure fixture. It preserves original HOME and uses an owned temporary
npm cache; no packages or models are installed. Runtime commands, base/build
configuration, public API and shared counter remain unchanged. All17 current
product template formatters were inspected; node-web was the sole unbracketed
outlier, so no broad legacy-format allowance is added.

L0: `python3 scripts/run_local_e2e.py` (with Node/npm and SDK installed). `e2e_test.py` uses the real server HTTP API to upload a 4 MiB noisy Node application, assert HTTP response through both named command and independent process API, inspect stderr logs, stop/rebind, run npm start/dev, build an artifact and read it via files API. It asserts missing-entry, malformed arguments, unknown command, duplicate launch, nonlocal paths, build nonzero/timeout and readiness timeout errors. Cleanup always stops the service and deletes only the test-owned UUID directory. The bundled smoke independently asserts a real exact HTTP response and stops the sample.

2026-10-16: focused repository L0 harness `_run_one(node-web)` passed all 60 assertions with the local server SDK checkout (0.3.0), Node 22.22.2, isolated npm 10.9.4 and httpx 0.28.1. This does not constitute Node 20 image validation. L1 pending: Docker is unavailable; a future build must show the pinned server and base runtime versions. L2 pending: `python3 scripts/express_e2e.py node-web` invokes smoke through CLI and Python SDK, expects `node-web ready`, and may write evidence only after success. No cloud provider is recorded. L3 model acceptance is inapplicable to this HTTP runtime. L4 is unverified and not claimed.
