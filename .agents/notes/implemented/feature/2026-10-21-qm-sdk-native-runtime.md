# Decision: original QM headless harness and Agent Sandbox backend

Status: implemented. Refs https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/44 and https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/45.

## Problem

The QM Issues request its genuine agent loop on Express and a real SDK-backed QM sandbox adapter. Original default local backend uses Docker; copying a configuration placeholder or relabeling a generic chat agent does not qualify either requirement.

## Decision

Run a bounded unchanged original QM Pi harness/tool loop with an authored backend implementing the original Sandbox interface through the actual Agent Sandbox Node.js HTTP SDK. Both run inside one newly owned Express sandbox, without cloud credentials forwarded to model tools. Explicit approved compatible provider, private per-call state, no delegated agents or Slack/email messages. Qualify only the exact slice actually run; full multiplayer web/Slack/Postgres services are separate.

## API Design

qm-sandbox backend operations provision/run/read/write/list/remove/teardown through actual SDK server APIs, with bounded paths/content/deadlines and exact owned state cleanup. qm original native harness command must use unchanged createPiHarness and original createToolContext, explicit original custom-provider registry and the same SDK adapter. Scalar public commands, exact native terminal/transcript evidence, API scopes and resource limits must be frozen and tested before cloud acceptance.

## Alternatives considered

Original default Docker local backend cannot simply be claimed on Express. Original buildApp does not expose a sandbox override; directly embedding its exported native harness/tool context is the bounded integration seam being evaluated. Original E2B backend does not establish Agent Sandbox SDK compatibility by name alone. A generic substitute agent or fabricated backend result is rejected.

## Dependencies

Original yc-software/qm source deef9b8b1e2b85bd4166dd833604bb31bcb8e255; original package lock, public MIT license and full source must be retained. Node>=24.15.0/npm>=11.10.0. Original custom provider supports OpenAI Chat Completions, Responses and Anthropic; use explicit approved Chat Completions, not a default vendor endpoint. Agent Sandbox Node SDK source90b5187dca84fca78d75d3045896482540641c72; npm0.1.0 returned404, so do not invent a published install. Build exact original SDK source using its own lock and scripts. Source archive hashes in verification are controller measured, not upstream-published checksums.

## Test Strategy

Authored path/content/route/credential/ownership/deadline regressions and original interface type checks; actual non-root image with native source/SDK hashes; canonical immutable native steps, officialREADY, actual Python SDK-created Express, CLI/SDK native backend smoke/fullHTTP. Only a fresh owned target runs original model/tool code. Real QM code repair must preserve original test bytes, produce new report/exact nonce artifacts and independently pass all original/held-out post-return cases. No native/model/provider pass inferred from source-only tests. Independently verify native/private/listener/project/outer/OSS absence.

## Acceptance criteria

- Original QM and SDK source/lock/license identity; no Docker-only backend falsely qualified and no substitute agent.
- Genuine original QM loop/tool calls use the actual SDK backend; complete required Express/image/HTTP/native model/independent artifact checks pass.
- Both templates have complete bilingual docs/design/catalog/spec/records, exact limits and truthful qualification.
- Every mandatory current-head check/review passes before normal verified merge; Issues close only after delivered acceptance.

## Evidence
[Final acceptance](../../../evidence/verify/2026-10-21-qm-native-final.md), [current43matrix](../../../evidence/verify/2026-10-21-current-native-http43.json), and source-bound template receipts. Runtime fff24f25dbe37b1ccc2110b81879e467645e5095 passes both actual L1 builds and complete remote CI; final record-only revision requires its own current-head checks before normal merge.
