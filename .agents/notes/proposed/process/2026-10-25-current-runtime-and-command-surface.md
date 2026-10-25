# Current published runtime and canonical template commands

Status: proposed

## Problem

The public a2 SDK's one-shot readiness check could reject a live starting application; the SDK owner fixed this in published client/server 0.4.0a3. The subsequent published 0.4.0a4 patch corrects stale SDK parameter docstrings without changing runtime behavior. Template Dockerfiles must use the current public package. Many current README/design paragraphs still described retired Git server archives or wheel injection despite the newer direct-PyPI recipes. Four templates retained pre-release command-name forwarding wrappers. QM consumers also pinned an older project Node SDK source that omitted reviewed transport-binding, redirect and error-redaction fixes.

## Decision

Install exact published agent-sandbox-server==0.4.0a4 from the official PyPI index in all 48 declared Docker recipes (46 public source templates, skeleton, and the Python portable profile), and increment each of the 47 affected manifests by one patch. Keep a single current startup contract. Remove the four verified forwarding names: opencode, amp, codex and OpenClaw gateway; retain opencode_run, amp_execute, codex_exec and gateway_* as their canonical commands. Do not add compatibility or migration modes. Preserve genuinely distinct Codex Agent API one-shot and Qwen Python-script capabilities; correct their misleading compatibility wording.

## API Design

Removed project aliases are absent from command discovery and return HTTP 404. Canonical commands retain their signatures and implementation. Each affected complete HTTP controller checks the removed-name boundary alongside existing canonical business assertions. All current bilingual runtime instructions describe the published server recipe; historical receipt inputs remain immutable and README historical descriptions use past-tense limits. The manually injected source-runtime diagnostic is only a pending user retirement decision and is not removed here.

## Alternatives considered

Keeping wrappers for a not-yet-stable interface contradicts the user's requested current-only API. Adding a version selector, fallback wheel source or another runner would increase complexity. Replacing all Git pins with npm would invent publication: @agent-sandbox/sdk is not currently published. QM therefore keeps one immutable source input, updated to the reviewed current Node SDK commit with measured archive/identity hashes; original package/lock files are unchanged and verified byte-for-byte.

## Dependencies

Published Python SDK a4 corresponds to https://github.com/Alibaba-Agent-Sandbox/python-sdk/commit/100da4661809f91a5d50e2722d1f4a8d4da3b131 (public package installation is independently checked). Current Node source is https://github.com/Alibaba-Agent-Sandbox/nodejs-sdk/commit/63d7cd8ece221b9f968eef51eeb932ea334c90d3. Native step/current shared-consumer cleanup depends on https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/224 and the CLI 0.5.4 typed template-not-found fix. Runtime and acceptance tracking remains https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/221; the native-step contract is tracked in https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/223.

## Test Strategy

Fresh official-PyPI client/server installation, pip check and imports; actual local HTTP discovery/invocation regressions against all four real command modules; current canonical privacy/process regressions; actual current Node SDK archive verification/build and HTTP adapter fixtures; all declared-profile server pins, specification/catalog/document checks and complete required image/CI gates. After official CLI 0.5.4 is publicly available and this source is merged, use the existing native Express and public OpenSandbox runners for fresh full-source matrices. Historical and candidate checks never certify the newer published inputs.

## Acceptance criteria

- All 48 declared recipes install exact public a4 through the official index; all 47 manifests increment minimally.
- Current docs agree with recipes, and only the four canonical project command surfaces remain.
- Current Node source/locks/notices are measured and preserved; no fabricated npm fallback is introduced.
- Actual local regressions and all current-head required CI pass; independent exact owned cleanup remains mandatory for real-provider acceptance.
- Fresh public-source/provider matrices retain every failure, explicit skip and unknown cleanup. Provider-bound managed entries are not remapped to foreign providers.
