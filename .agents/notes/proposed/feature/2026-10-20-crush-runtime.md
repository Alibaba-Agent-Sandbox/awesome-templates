# Decision: pinned native Crush compatible-provider profile

Status: proposed

## Problem

[Issue65](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/65) lacks a runnable native template. The older nightly-only observation is obsolete: official stable0.98.1 exists.

## Decision

Use exact official GNU CPU assets/source and real CLI, private per-call compatible provider settings, default zero tools and explicit eight coding tools. Preserve FSL-1.1-MIT and notices without mislabeling it MIT/open source. No subagent work is enabled.

## API Design

crush_version/read-only crush_setup_check and typed crush(prompt,cwd,allow_tools,command_timeout) returning stdout/stderr/exit_code. See bilingual reference for limits/auth/cleanup. Refuse caller project Crush configuration before run because the upstream has no reviewed ignore-project-config switch. Explicit native local foreground mode avoids a reusable daemon.

## Alternatives considered

A dummy marker or CLI stdout is not model coding acceptance. Reusing caller configuration risks invoking shell/MCP hooks. Floating nightly installer cannot establish reproducible release provenance. Native max-turn flags do not exist; wall/per-response bounds are documented instead.

## Dependencies

Official Crush0.98.1 source8b1824282eccc78cc62c188c245cf375230a18ce, fixed x64/arm64 GNU assets, unchanged FSL license, SDK/server pinned source and Linux pidfd/procfs. No browser/GPU/model weights. Only explicitly configured compatible endpoint receives the selected credential.

## Test Strategy

Actual installed upstream CLI with authored local HTTP/SSE and deterministic write tool; exact tool names, version and caller config/home guards; native process deadline/overflow/descendants; structured controller regressions. L1/current-head CI, true SDK-created Express and strict real-model independent tests required before qualification.

## Acceptance criteria

All source/docs/image gates, exact-version actual Express CLI/SDK/full API and real model source edits/new artifact/original tests/held-out values, independent owned cloud cleanup; complete bilingual operations and immutable evidence; normal merge before Issue65 closure. Missing gates remain explicit.
