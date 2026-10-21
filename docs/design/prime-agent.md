# prime-agent

## Purpose

Run unchanged official stable Prime Agent0.10.0 headless coding with the original CPython REPL and explicit approved compatible model, entirely in an owned disposable outer sandbox.

## Capabilities

Named native version, original kernel/import check, read-only setup and bounded coding. Linuxx64 CLI/REPL slice only; daemon/recursive agents/subscriptions/research benchmarks remain outside qualification. Original print mode supplies no child host; runtime_wiring uses NoRlmChildren. [Pinned wiring](https://github.com/PrimeIntellect-ai/prime-agent/blob/763094e1b6a7c17450ee8399b06cda1853847ca5/crates/pa-core/src/session_engine/runtime_wiring.rs).

## Exposed API

[Complete scalar parameter/output contract](../../prime-agent/README.md#command-reference): prime_agent_version(), prime_agent_kernel_check(), prime_agent_setup_check(), prime_agent(prompt:required string1..32768UTF8bytes,cwd:optional existing contained string default empty,command_timeout:integer1..600seconds default300). Version executes original --version; kernel uses fixed supported interpreter with original protocol3/hooks/default imports. Coding uses original --offline --mode json --provider abx-approved --model explicit --thinking off --no-session --no-skills --no-prompt-templates --no-themes --no-context-files --cwd privateGit --print, anonymous stdin and real original ipython tool. Native cwd cannot load caller project provider overrides. Results preserve actual exit/status/settled events.

## How to build

[Dockerfile](../../prime-agent/Dockerfile): Alibaba FC generation2/Python3.13/Linuxx64, original SHA256-pinned stable release from [upstream.json](../../prime-agent/upstream.json), full original sidecars/notices,49-package hash lock in isolated /opt/prime-kernel. No floating native install script/uv/kernel dependency setup. Common server source e2cb27e24fde0a67112f82b8d44af463445a5d1a, non-root user, start_cmd agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py; ready_cmd agent-sandbox-server healthcheck --port 9000. No CMD/ENTRYPOINT. [Steps operation](../../docs/platform-steps.md) preserves exact immutable context/public asset hashes; no local Docker required for steps.

## Express feasibility

Feasible: slice

Limiting factor: Linuxx64 native CPython coding only; daemon-backed child sessions and research workloads are not accepted here.

Declared2vCPU/2048MB/non-root,8GiB guarded rootfs, no KVM/Docker/GPU/extra capabilities. Native kernel/model memory and full provider acceptance require actual gates; source-only checks cannot establish them.

## Risks

Native model code has outer-user OS authority; containment is not a nested security boundary. Minimal environment/private0700HOME/0600config, explicit approved provider and no operator credentials; kernel drops model key from inherited environment but same-user OS access remains. All key/base literals/JSON forms redacted. Offline startup and telemetry/discovery/refinement/factory disabled; no delegated child host. Serialized requests; whole-group/pidfd/nonce descendant cleanup on success,timeout,overflow,failure. Raw NDJSON16MiB/line1MiB, retainedstdout256KiB/stderr256KiB; caller artifacts persist until caller removes them. Client timeout/disconnect does not cancel native operation. Compatible model pricing unspecified.

## Test plan

L0:35authored boundary/terminal tests, source-onlyHTTP7PASS/nativeSKIP. L1 actual image installs exact archive/binary and49package lock, verifies original kernel protocol/default imports as non-root. L2 canonical SDK-created Express steps/officialREADY/CLI+SDK native smokes/fullHTTP and independent cleanup, receipts bound to exact runtime/context. L3 synthetic-key native routing first, then actual approved model repairs seeded existing source, preserves3original tests and passes4independent held-outs with new report/fresh nonce/native ipython terminal completion and post-return ACK. All generated code executes only owned remote target. No L4/daemon/recursive/research claim. Pending gates stay explicit until recorded.
