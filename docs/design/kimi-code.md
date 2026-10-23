# kimi-code

## Purpose

Implement Issue48's actual current Moonshot Node CLI in one Express sandbox. The official npm 2.2.0 package, executable help and environment-provider code were directly inspected on 2026-10-19.

## Capabilities

Keyless version/setup inspection and one bounded headless coding turn, private settings per invocation, buffered stream-JSON and explicit automatic tool permission. Ordinary shell/files/code/ports capabilities; no resumable session promise.

## Exposed API

kimi_version() returns upstream --version. kimi_setup_check() reports installed/pin and configuration flags without credential values. kimi(prompt required string, cwd default workspace, command_timeout default600 seconds in1..1800, allow_tools defaultfalse) runs --prompt/--output-format stream-json and requires explicit allow_tools=True because upstream prompt mode forces auto permission and rejects --auto/--yolo flags. Output capped at8 MiB per stream; nonzero/timeout/overflow errors are sanitized.

## How to build

Single Alibaba FC base; reuse verified Node24.16.0 architecture hashes, then install @moonshot-ai/kimi-code@2.2.0 and print version. Fixed server source, workdir/home/user/app, USER user and standard generation2 start_cmd/ready_cmd on9000. No CMD/ENTRYPOINT. Standalone context has commands.py and Dockerfile; step materialization must retain source and explicit Node setup.

## Express feasibility

Feasible: yes

Limiting factor: none for the process-based CLI; actual provider/model acceptance is still separately required.

No Docker/KVM/GPU/desktop required. Node>=22.19 is the upstream dependency and is satisfied by the checksum-pinned image install.

## Risks

Auto mode may edit files and execute tools with sandbox user authority. It is false by default and refuses prompt-mode invocation until explicitly true. Model base URL is explicit to avoid cross-provider key reuse. Each invocation owns its temporary Kimi home, excludes cloud/registry secrets, redacts output and kills same-group descendants before reaping the leader. Independent groups and remote model requests are outside local cancellation guarantees. Upstream2.2.0 is MIT; wrapper Apache-2.0. This is a real upstream CLI, not a replacement loop.

## Test plan

L0: actual pinned --version, typed HTTP, missing-model guard, process/timeout/credential/argv regression tests. L1: build actual image and assert Node24.16.0/Kimi2.2.0 as USER user. L2: real canonical Express deployment, version/setup through CLI and SDK, owned cleanup readback. L3: compatible-model turn fixes seeded calculator.py, creates REPORT.md and exact random artifact, leaves original tests unchanged and passes isolated original/held-out verification with post-response random ACKs. Missing/disabled required model fails; fixtures prove only verifier behavior. L4: not claimed.

Release readiness 1.0.1: align default and injected server SDK source to `e2cb27e24fde0a67112f82b8d44af463445a5d1a`; preserve historical receipts and require new image/workflow acceptance.
