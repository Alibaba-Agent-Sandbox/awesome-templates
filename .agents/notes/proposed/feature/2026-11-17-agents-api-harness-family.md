# Decision: Standalone native Harness recipes sharing one managed API

Status: proposed

## Problem

The single agents-api recipe installs Codex and Qwen together and defaults to Qwen. The user requested named native Harness recipes, a shared protocol, complete matching configuration/documentation, independent adversarial review and eventual verified publication.

## Decision

Rename the source to agents-api-codex and generate five standalone peers for qwen-code, claude-code, qoder, opencode and official deepseek-harness. Preserve Gateway/Worker/Dispatcher, PostgreSQL, receipts/epochs, frozen revision routing and drain-aware cleanup. Each Guest installs only its selected pinned CLI. Maintain shared files in the Codex recipe and a closed generator source list, with no sibling runtime dependency.

## API Design

All six use agent-sandbox-managed-agents/v1. Runtime adapters, credential names and model endpoints differ. Bootstrap binds an exact adapter-specific model environment allowlist into real Session snapshots. Only Worker gets model secrets; Gateway gets the business-key digest. Qoder uses PAT without a fake endpoint. DeepSeek uses official DSH Messages, distinct from the old repository-owned tool loop. Busy ordinary input remains409; explicit submissions queue another turn rather than claiming steering.

## Alternatives considered

Copying directories without native adapters is not adaptation. Installing all CLIs everywhere enlarges images and obscures credential ownership. Replacing official DSH with the existing local loop misidentifies the product. Generating from arbitrary working-tree files risks copying private dotenv variants; use a fixed source list. Do not weaken model-env admission to accommodate an incomplete bootstrap.

## Dependencies

Tracking: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/309.
Native resource producer: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/311.
Engine: https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/pull/249.
SDK source base: https://github.com/Alibaba-Agent-Sandbox/python-sdk/pull/164.
New recipes target paired client/server0.4.0a8; this is an unpublished candidate, not a completed release.

## Test Strategy

Strict catalog/spec validation, actual JS/Python contract parity, existing shared script/release/smoke suites and standalone family bootstrap tests. Reproduce missing modelEnvAllowlist through real ManagedService Session creation and actual backend admission before fixing it. Native CLI, image, cloud, real model, retained Session upgrade and independent cleanup require their own evidence. Preserve failures and skips.

## Acceptance criteria

All six identities/configurations/docs agree and generated projects work independently. Complete two independent post-implementation review rounds, fix findings, verify candidate package/images and real hosted business flows including old Session routing, then publish only after required CI/review gates. Until those gates pass, keep Draft and Issue309 open.

## Evidence

[Verification](../../../evidence/verify/2026-11-17-agents-api-harness-family.md).
