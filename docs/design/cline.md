# cline

## Purpose

Expose real Cline CLI3.0.73 coding through named commands in a newly owned Express sandbox, tracked by [Issue66](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/66). Native CLI slice, not the separately versioned editor extension or hosted service.

## Capabilities

Actual unmodified official Linuxx64/Bun binary and npm wrapper; native headless JSON/yolo tools, file changes and native NDJSON terminal result. Explicit OpenAI-compatible provider/model/base/key; no Cline hosted provider/login. Actual output is buffered with exit_code, not fabricated streaming or a substitute agent.

## Exposed API

[English](../../cline/README.md#command-reference) and [Chinese](../../cline/README.zh-CN.md#命令参考) enumerate every scalar parameter/default/bound/result. cline_version returns actual3.0.73 after fixed native SHA256; setup only presence booleans; cline(prompt,cwd='',command_timeout=300) validates cwd containment/deadline/input, then invokes fixed native argv with anonymous prompt stdin and no shell. Own config/data/HOME/session/team paths, global telemetry/update/logging off, empty own MCP settings. Serial operation lock protects lifecycle. No provider key in wrapper settings or argv; native documented env auth. Nonzero code retained and never accepted as L3 success.

## How to build

[Dockerfile](../../cline/Dockerfile): Alibaba basev0.0.49, generation2, Python3.13, official Node24.16.0 with SHA256, npm ci full integrity lock for cline3.0.73 and its exact native/core packages. Actual binary SHA2561ff8841d17d4d83763134c193d414e4f7fcf2ef56af759e5ebbe96727fc2c8f7 verified both build/runtime. Published server package 0.4.0a3; explicit serve/healthcheck9000, WORKDIR/home/user/app, non-root user, owned workspace/home/user/workspace, no CMD/ENTRYPOINT,8GiB rootfs budget. Steps use immutable public COPY with every hash; large package lock requires publishing exact source first.

## Express feasibility

Feasible: slice

Limiting factor: Linuxx64 native/Bun compatibility and authorized compatible model tool calling. No nested VM, Docker, GPU or special host permission. CPU2/RAM4096. Native--yolo is explicit unsupervised tool approval, not read-only/tenant isolation; native OS permissions can reach beyond validated cwd. Use only trusted disposable sandbox scope. No editor extension/hosted Cline claim.

## Risks

Model endpoint explicit HTTPS or authored local HTTP, no userinfo/query/fragment. Wrapper forwards only the approved model key as OPENAI_API_KEY, selected certificates and private runtime state; no caller cloud/GitHub/account tokens or binary override. Prompt uses anonymous memory/stdin and literal argv; output redacted before returning,256KiB per stream. Group/marker/pidfd cleanup reaps detached children, private HOME/config/cache/data/team state removed on all paths. Workspace artifacts deliberately persist for caller; no automatic project rollback. Original caller HOME/credentials stay untouched. Apache2.0upstream license retained at exact CLI tag/source; no relicense or vendor PAT invention.

## Test plan

L0 actual authored input/config/symlink/credential/profile/stdin/exit/redaction/private-state/serialization controls plus strict docs/spec. Real keyless native binary/help validates flags/version only. L1 actual Alibaba image must verify exact native SHA and image-user cline_version; install alone insufficient. L2 canonical native steps → official READY → Python SDK Sandbox.create → CLI/SDK named version → independent owned sandbox/template absence. L3 new owned model server: real native run_result completed, existing source repair, unchanged original tests, fresh report and exact random artifact, complete independent original3tests and held-out post-return fresh ACK evaluations inside cloud only, owned project/listener/private profile and outer resource absence. Local models/markers/fake CLI/source fixtures never qualify native L3. Required cloud/model gates remain mandatory; current actual acceptance is recorded below.

Primary provenance inspected2026-10-20: [official npm3.0.73](https://registry.npmjs.org/cline/3.0.73), [CLI source tag](https://github.com/cline/cline/tree/cli-v3.0.73/apps/cli), exact sourcecommitc718573538d76310f464541617ab665108a6c999. SHA512-integrity-verified native package; actual3.0.73version/3993-character help/777-character auth-help executed without model credentials in private local state, then completed native fixture removed with digest/restoration record. Pin differs from survey's separately versioned extension; wrong similarly named package was excluded after inspection. That initial keyless inspection was not cloud/model qualification; current actual acceptance follows.

Pinned3.0.73 JSON preflight runs before piped stdin parsing. Runtime1.0.1 supplies one fixed, non-secret positional sentence; actual task text remains anonymous stdin, appended by upstream. Real1.0.0 SDK cloud runs reproduced the premature preflight exit; no model success is inferred.

Current1.0.2 source691c7d40b73863c38737f2f893c88f423617eddc passed actual SDK-created canonical native Express steps/full HTTP8/0/0, synthetic-key native exact endpoint/model/auth and fixture cleanup, then real qwen3.8-flash coding17/0/0: existing source repair, original tests byte-identical, new report/exact nonce artifact and full original3tests/4held-outs with fresh post-return ACKs. Own project/process/listener/private native state and outer sandbox/template independently absent. [Final evidence](../../.agents/evidence/verify/2026-10-20-cline-native-final.md).
