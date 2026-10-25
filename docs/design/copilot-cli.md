# copilot-cli

## Purpose

Run pinned native GitHub Copilot CLI as an authenticated cloud file-editing service with explicit compatible BYOK, without using GitHub credentials. Own the target sandbox and each per-call process/profile.

## Capabilities

Named version/setup/prompt commands, target file reads and explicitly enabled edits. Default native tool list view/glob/grep; editing adds edit/create/apply_patch. Shell/network/delegation/interactive/resume/plugin/ACP workflows are outside this slice. The CLI's path policy is not an OS jail.

## Exposed API

The [bilingual command reference](../../copilot-cli/README.md#command-reference) owns exact parameter/result/bounds: copilot_version(), copilot_setup_check(), copilot(prompt,cwd="",allow_write=false,command_timeout=300). Native argv fixes JSONL output/noninteractive mode and closed tools, disables auto-update/telemetry/MCP/instructions/remote, retains nonzero native exit, bounds each stream256KiB and execution1..600seconds. No arbitrary flags or account login. SDK examples explicitly start their own model-configured9010 server, separate from prewarmed9000.

## How to build

[Dockerfile](../../copilot-cli/Dockerfile), generation2/base/start_cmd/ready_cmd from [manifest](../../copilot-cli/template.yaml), non-root user, Linux x86_64. Exact @github/copilot and native-linux-x64=1.0.100 plus detect-libc use [npm lockfile](../../copilot-cli/package-lock.json); npm ci --ignore-scripts --omit=optional. Native binary/license are unmodified. Server package version is pinned in the Dockerfile. Provider-owned Dockerfile/steps preparation preserves source pins.

## Express feasibility

Feasible: slice

Limiting factor: compatible streaming/tool-call model endpoint; only Linux x86_64 native package is installed.

2vCPU/2048MB CPU-only non-root Express needs no Docker daemon/GPU/KVM. Original Issue64's survey prerelease is superseded by verified public stable1.0.100 package metadata and pinned native help. Official [BYOK](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/use-byok-models) requires no GitHub authentication; this template deliberately selects explicit OpenAI-compatible completions/http. Fixed native help confirmed flags and provider wiring. Actual L1 image builds and current-source SDK-created Express native steps/model17 now pass; [final proof](../../.agents/evidence/verify/2026-10-20-copilot-cli-native-final.md) separates those scopes.

## Risks

Model/cloud credentials stay separate. Capture explicit model settings at server startup, filter child environment, omit GitHub tokens and key-command/headers, native secret-env filtering plus wrapper exact key redaction. Private HOME/XDG/temp/cache/logs are removed only after group/marked detached worker cleanup; preserve caller project files. Generated source executes only in fresh owned remote sandboxes during acceptance. Native upstream [custom license](../../copilot-cli/UPSTREAM-LICENSE.md) remains independent: redistributed unmodified as part of this authenticated API/file-transfer/sandbox service, never as a standalone primary product; retain all notices. No blanket open-source relicensing or GitHub service entitlement is claimed.

## Test plan

L0 authored substitutes exercise validation, literal argv, closed tools, credential filtering, nonzero/redaction, timeout/detached child cleanup/unrelated process survival. Source-only HTTP reports missing native binary explicitly; no host model calls. L1 actual image installs exact packages and checks real binary. L2 actual Express SDK creation plus CLI/SDK smoke and owned sandbox/template cleanup; separately labeled step mode. L3 real native model changes seeded source, creates report/exact fresh ABX_E2E artifact, preserves original tests, then independent cloud original/held-out evaluations succeed with fresh post-return acknowledgements. Generated source never runs on operator. Other providers/architectures remain unverified. Current-head CI/normal merge and complete Issue64 criteria required for closure.
