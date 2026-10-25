# deepagents

## Purpose

Run actual pinned native DeepAgents in an owned sandbox using its local filesystem/shell backend and explicit compatible-provider model.

## Capabilities

Version/setup/native deepagents(task,cwd,allow_tools,command_timeout), structured stdout/stderr/exit_code; standard files/shell SDK. Default0 tools, explicit8; no general-purpose/custom/async subagents or remote sandbox backend.

## Exposed API

[Complete reference](../../deepagents/README.md#command-reference). Fresh driver process imports actual create_deep_agent/ChatOpenAI/LocalShellBackend; private stdin configuration. Chat-completions endpoint explicit, no Responses assumption. Graph recursion40, model60seconds/0retry/8192tokens, shell120seconds/100000bytes, outer wall1..1800seconds and256KiB per output. No CLI console entry invented.

## How to build

[Dockerfile](../../deepagents/Dockerfile), FC generation2/Python3.13, exact hash-locked DeepAgents0.7.25/langchain-openai1.7.2 and transitive dependencies; pip check/version validation. Preserve all installed license notices, published server package 0.4.0a4; writable workspace/non-root, serve/healthcheck9000,8GiB rootfs gate. No CMD/ENTRYPOINT.

## Express feasibility

Feasible: slice

Limiting factor: explicit compatible endpoint/model key and real native dependency/runtime acceptance. No browser/GPU/KVM/Docker required;2vCPU/2GB. LocalShellBackend operates inside the owned cloud sandbox, never an operator host with a real model. No other provider claim.

## Risks

Private HOME/config/data/stdin, filtered runtime env and independently filtered shell environment. Virtual filesystem mapping does not restrict shell authority. No skills/memory/profile imports. GeneralPurposeSubagentProfile(enabled=False), no provided subagents and exact observed tool tests prevent delegation. Each process registers profile once because upstream registration merges exclusions. Identity-pinned marked-worker/group cleanup; sandbox destruction final boundary. MIT upstream and transitive notices retained.

## Test plan

L0 actual0.7.25/native tool discovery0/8, no task, authored actual write_file and independent file bytes, readonly version/setup, caller home preservation, key/path/types/limits, process descendants/output/deadline and structured controller regressions. L1 hash/version/image/rootfs. L2 true SDK-created Express READY/CLI/SDK/full HTTP and independent cleanup. L3 real model source edit/report/unchanged original tests/fresh held-out checks; L4 only when another provider actually executed. Native steps receipts separate from preparation.

### Executed qualification

Version1.0.0 actual SDK-created verified image and compatible qwen3.8-flash model17/0/0 passed source edits/report/original tests/fresh held-out calculations and independent owned sandbox/template/registry cleanup. [Canonical receipt](../../deepagents/evidence/express-2026-10-20.json). The [separate native step attempt](../../deepagents/evidence/verification-steps-2026-10-20T112245Z.json) failed to reach READY within1200seconds, last official state building; no sandbox created. Owned template deletion and independently rechecked cloud absence passed. No inner cause or universal RUN cap is inferred.
