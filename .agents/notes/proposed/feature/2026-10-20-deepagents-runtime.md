# Decision: native local DeepAgents without delegation

Status: proposed

## Problem

[Issue67](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/67) has no working template and an unverified headless entry. Actual installed0.7.25 provides create_deep_agent and LocalShellBackend; no console script is assumed.

## Decision

Pin all package versions/hashes, run an explicit compatible-chat driver in a fresh private process with local backend and disabled general-purpose/custom/async subagents. Default zero tools, explicitly permit exact eight observed native tools. No real model on the operator host.

## API Design

Read-only version/setup and deepagents(task,cwd,allow_tools,command_timeout) structured output. Full bilingual reference covers graph/model/shell/process bounds, ownership and auth. Keep venv Python path instead of resolving the executable symlink. Explicit ChatOpenAI uses chat completions; no saved profiles/skills/memory.

## Alternatives considered

Unverified console scripts or static output markers do not prove the library. Default subagent machinery violates this task's no-delegation scope. First actual discovery found an additional delete tool, now covered by default exclusions. A research profile reused in one process accumulated exclusions; fresh per-turn worker prevents cross-call registration leakage. Virtual filesystem is not shell isolation.

## Dependencies

DeepAgents0.7.25, langchain-openai1.7.2 and complete SHA256 lock generated with uv0.11.28/Python3.13; actual pip install/pip check. MIT upstream/notices retained. SDK/server pinned e2cb source and FC base. No E2B/OpenSandbox backend, browser or GPU.

## Test Strategy

Actual installed library/compiled graph and authored HTTP/write_file fixtures0/8 tools, no task, actual retrieved file bytes. Private wrapper guards/state/process regression and structured controller tests. Image/current-head CI and real SDK-created Express/strict real-model source edit/report/original tests/held-out checks remain required.

## Acceptance criteria

Complete source/docs/image gates, actual Express SDK-created CLI/SDK/full API and strict real-model edit/report/original tests/independent values with zero failed/skipped required checks; independent owned cleanup; precise steps feasibility receipts; normal verified merge before Issue67 closes.

Implementation follow-up: actual separate-session backend child leakage was reproduced before propagating a non-secret per-call ownership marker. Hash-lock install acceptance extends the strict checker only for validated simple local COPY/file/exact-pin/SHA256 syntax; actual pip enforcement/pip check and image gates remain authoritative. Native backend output limit is post-capture truncation, not a peak-memory promise.
