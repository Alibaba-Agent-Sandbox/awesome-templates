# grok

## Purpose

Expose genuine official xAI Grok Build coding in an owned disposable Express sandbox through named commands. Issue40 originally lacked a reproducible official installer; current npm @xai-official/grok1.0.62/native packages provide integrity-pinned distribution. Community grok-dev is a separate product and is not substituted.

## Capabilities

Shell/files/code/ports and genuine headless native source editing with an explicitly approved compatible model. No hosted Grok model, subscription, desktop, web search, subagent, workflow or multi-provider qualification. Outer sandbox owns the native process authority.

## Exposed API

Both [English](../../grok/README.md#command-reference) and [Chinese](../../grok/README.zh-CN.md#命令参考) document scalar bounds/defaults. grok_version verifies actual native SHA256 and exact1.0.62/build marker; setup returns presence booleans only. grok(prompt,cwd='',command_timeout=300) validates UTF8≤32768bytes/cwd≤4096bytes/1..600seconds and executes exact native flags. JSON/nonzero exit/stdout/stderr are buffered and bounded, not streamed. Private model alias uses actual native custom model api_backend chat_completions and env_key; keys are never argv/settings values. Prompt via anonymous stdin and --prompt-file /dev/stdin.

## How to build

[Dockerfile](../../grok/Dockerfile): Alibaba generation2/v0.0.49, SHA256 Node24.16.0, full official npm integrity lock @xai-official/grok1.0.62/native optional package. No upstream install scripts: authored Node Brotli extraction creates fixed /opt/grok/bin/grok; native SHA2562a46d9e4d7ebd7a9cff7f95716714b19dad5f21dd2a497822400b1fb128969aa required. Official Apache2.0 license and packaged third-party notices retained. server package 0.4.0a6, user runtime, start/health9000, no Docker CMD/ENTRYPOINT. Source snapshot2bdd1d6a6369de0e8c68132ea4539e9abd9e14a8 is contract research, not claimed as native build1474f9cbdd91.

## Express feasibility

Feasible: slice. Limiting factor: hosted vendor credentials and product scope, not VM support. Linuxx64,2vCPU,4096MB, no nested Docker/KVM/GPU. 8GiB image budget; about10GiB Express rootfs. Genuine native coding CLI with the compatible-model slice independently qualified in the current acceptance below. --sandbox off is explicit: native tool authority remains within the disposable outer sandbox. Hosted/vendor models require their own credentials and independent validation.

## Risks

Per-call private0700 HOME/GROK_HOME and0600 TOML, fixed binary/SHA, no caller credentials/config. Explicit HTTPS base or literal local HTTP fixture only, no userinfo/query/fragment, approved key only named environment. Disable leader/update/telemetry/trace/memory/workflows/subagents/web; fixed coding tools allowlist. Native shell environment core/default secret exclusion. Arg cwd containment is not a native tool OS boundary. Serialized process group/nonce marker/pidfd cleanup includes detached workers and removes private HOME after success/failure/timeout/output overflow. Native output256KiB/stream and key/base redaction; actual workspace artifacts intentionally persist, no rollback.

## Test plan

L0 authored invalid config/input/symlink/credential/privateTOML/literalstdin/nonzero/redaction/state cleanup controls, actual Python SDK HTTP scalar/Bearer serialization and terminal JSON false-positive guards. Actual keyless pinned binary --version/help only proves identity/flags. L1 image actual native SHA/version. L2 source-bound canonical steps→official READY→actual Python SDK Sandbox.create→CLI/SDK native version→full HTTP→independent owned resource absence. L3 real native run end_turn/positive num_turns/session/request IDs, seeded existing bug repair, original tests byte-identical, fresh report/nonce artifact, complete original3tests and held-outs with post-return random ACK, generated code only on new remote sandbox. Own project/listener/private native state/outer sandbox/template absence required. Every historical failure/skip stays explicit; current qualification is recorded below.

Current1.0.1 at57e7efdb7c1c79f55500faf3e32fb27487b0761f passed actual SDK-created canonical native Express steps/full HTTP8/0/0, synthetic-key native route/auth/cleanup preflight, then real qwen3.8-flash source repair/report/exact nonce artifact/original byte identity/original3tests/4held-outs with fresh post-return ACKs:17/0/0. Own native/private/process/listener/project/outer sandbox/template absence independently confirmed. Exact-source L1 native image-user version/SHA256 PASS, run39488718009. No xAI-hosted model/subscription/other provider or actual-image model deployment claim. [Final evidence](../../.agents/evidence/verify/2026-10-20-grok-official-native-final.md).
