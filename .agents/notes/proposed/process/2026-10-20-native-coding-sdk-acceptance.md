# Decision: Current native coding image and SDK acceptance

Status: proposed

## Problem

Existing coding templates have genuine historical model runs but current workspace profiles only have basic step receipts. [Issue17](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/17) requires current exact-source image, actual SDK creation, useful native behavior and independently confirmed cleanup before closure.

## Decision

Revalidate the unchanged runtime and independent strict controller using a completed exact-source CI Docker archive. Use Sandbox.create for the owned READY template and SDK named commands. Inject real compatible-model settings into an explicitly started owned server inside the sandbox because a prewarmed server does not adopt shell/create-time environment automatically. Execute the model-generated code and independent verifier only in the owned cloud sandbox. Keep source/runtime/model/basic acceptance scopes separate and preserve all historical failures.

## API Design

No runtime/API/version change. OpenCode2.0.1 retains pinned1.19.0 CLI, explicit provider configuration, headless run, exact-session continuation and interpreter-owned serve lifecycle. SDK creation and native named-command transport are verified independently of the strict external HTTP model controller. Existing documented native step operations remain available.

## Alternatives considered

Historical source-only proof or basic/version smoke cannot establish current-image model behavior. Running generated code on the operator is rejected. Rebuilding without exact source, skipping independent assertions or treating cleanup acknowledgment as absence would weaken required acceptance.

## Dependencies

Public image export at exact sourceca3118e5123e7ce2ae2e43e2a8a05c88ecf3653d and common injected servere2cb27e24fde0a67112f82b8d44af463445a5d1a. Native CLI and SDK source installation/provenance follow existing guides. Real model credentials remain process-local and are sent only to the operator-approved compatible endpoint. No product code changes.

## Test Strategy

Verify GitHub artifact/ZIP/archive/source/non-root identity, owned private-registry digest before registration and after runtime, official READY, SDK creation and CLI/SDK basic commands. Strict real-model checks require source edits, new artifacts, unchanged original tests, independent fresh held-out assertions, final completed steps and exact-session continuation. Independently read back owned sandbox/template/registry absence. Run source/protocol regressions and mandatory latest-head CI.

## Acceptance criteria

Current exact-source image/SDK/native/strict-model acceptance passes without required skips; ownership cleanup is independently confirmed; bilingual qualification links and records agree; latest-head CI passes and the normal scoped PR merges before closing the corresponding original Issue.

## Evidence

[Verification](../../../evidence/verify/2026-10-20-native-coding-sdk-acceptance.md).
