# swe

## Purpose

Make one real SWE-bench instance usable in a disposable non-root Express sandbox without claiming to reproduce official Docker scoring. Issue: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/35.

## Capabilities

Official mini-swe-agent 2.4.6 CLI, explicitly authorized local shell actions, one pinned Flask snapshot, original benchmark test patch and 60 exact test node IDs, independently reconstructed evaluation, source patch/report artifacts and scoped cleanup. No Docker, full dataset, system-package installer, caller-provided test shell, arbitrary instance checkout or gold solution patch.

## Exposed API

See the complete typed/default/range table in [README](../../swe/README.md#command-reference). `swe_version` calls actual `mini --help` and distribution metadata; `swe_setup_check` returns booleans; `swe_prepare(instance_id="pallets__flask-5014")` reproduces the baseline; `swe_run_agent(run_id, allow_execution=false, max_steps=12, command_timeout=300)` runs the actual CLI with absolute installed default config plus a private JSON-compatible YAML config; `swe_evaluate(run_id)` applies only the supported source diff to a fresh original checkout; `swe_report(run_id)` returns that report; `swe_cleanup(run_id)` removes only the opaque owned run. Same-run operations refuse concurrent use.

## How to build

[Dockerfile](../../swe/Dockerfile) preserves the Alibaba base/Python 3.13/Node20, pins mini-swe-agent 2.4.6 and LiteLLM 1.82.6 in an agent venv, and uses official SHA-pinned python-build-standalone20241016 Python3.11.10 for an independent Flask evaluation venv. It downloads only the 692792-byte official Flask archive, checks SHA256 `b1a4c83b7d12981b81e5f8d2028a73eacfbd153f4e425504c254a6f177b99997`, installs the exact server source wheel/fallback and leaves `USER user` with no CMD/ENTRYPOINT. Generation2 uses the required port9000 serve/healthcheck commands. New9010 processes in the usage docs receive explicit model configuration because a prewarmed9000 process may precede create-time envd settings.

## Express feasibility

Feasible: slice

Limiting factor: official per-instance Docker environments and their original Python/dependency image are not reproduced.

The specific `pallets__flask-5014` source archive and test patch fit the non-root 2CPU/2GB sandbox. The initial actual Python3.13 image yielded2PASS/58ERROR (pkgutil.get_loader deprecation under original filterwarnings=error). The test patch/filters remain unchanged; evaluation now pins the original instance Python3.11.10 via official x86/arm archive hashes. The Debian system and package pins still differ from the full original Docker environment, so this remains a local portability slice, not an official score. A real baseline of exactly1FAIL/59PASS is required before allowing a model repair. Evaluation reconstructs original source plus original tests in another directory and copies the fixed test venv. It requires all60 unique declared identities, no skips/errors and all passes before `resolved_slice=true`. Every report says `official_benchmark_score=false`. Broader SWE-bench/SWE-agent/SWE-rebench support remains open, not a global Express blocker for this bounded workflow.

## Risks

mini executes bash, so explicit `allow_execution=true` grants normal user filesystem/network access in this owned sandbox. A supported-diff allowlist restricts evaluator input, not agent writes. Do not use the wrapper as an OS isolation boundary. The environment extension preserves the official LocalEnvironment protocol and completion sentinel but keeps ordinary children in the CLI's owned process group; action env omits model/provider keys. An action can deliberately setsid/daemonize or read same-user processes, so arbitrary malicious code cannot be contained by CLI timeout. Final owned sandbox destruction is the cleanup boundary. No HOME replacement or shared-store writes occur. An official private global-config directory plus dotenv disable prevents implicit profile loading. Agent configuration/trajectory is private and removed in finally; subprocess errors omit logs, configured secrets refuse patch persistence, and reports contain fixed test names/counts only. Client disconnect does not cancel a synchronous command.

## Test plan

L0: scoped command and HTTP-harness regressions (real Linux process cleanup, locks/path/type/permission negatives, missing/duplicate/skipped test identity and missing target model configuration negatives) plus scoped HTTP contract smoke. L1: actual image CI must build with installed mini2.4.6 and server source pin. L2: canonical Express deploy→READY→SDK/CLI named smoke→owned cleanup remains a distinct gate. Supplemental source-runtime/actual-image runs must keep separate provenance and cleanup records. L3: real compatible Qwen model; baseline1FAIL59PASS→actual mini source edit→fresh evaluator60PASS→SDK files patch/report retrieval; no marker-only success. L4: none claimed. Full official Docker evaluation and other providers remain unverified.
