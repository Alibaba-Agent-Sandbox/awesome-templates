# Decision: Current Express acceptance CLI contract

Status: implemented

## Problem

The active acceptance runner used root --json, create --template/-y and kill -y against the standard Express CLI. It also expected the native template inventory and JSON creation shapes, allowing expensive deployment before command incompatibility surfaced.

## Decision

Preflight the actual selected CLI with read-only command help before cloud mutations. Use standard per-command template JSON format, exact aliases/templateID schema, positional detached creation with single-ID parsing and standard kill. Retain private ownership journals, independent readback, ambiguous-response recovery and explicitly pinned historical workflows.

## API Design

Runner argument arrays now match standard Express. Explicitly select alicloud-express in subprocess argv, respecting harness ownership even if host config chooses another provider. CLI timeout is validated >=30 before build; SDK mode retains its existing positive-timeout contract. No template/runtime contract version changes.

## Alternatives considered

Forcing every operation through --native would preserve the old lifecycle instead of testing the documented default. Accepting arbitrary output or unknown inventory shapes can misidentify resources or falsely claim absence. Parser-only mocks cannot verify executable compatibility.

## Dependencies

The pinned standard CLI contract at https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/tree/6df41f624249c316654fbd5c6d36c34a7beca0b8. Related guidance fix: https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues/109.

## Test Strategy

Update ownership/image/SDK controller regressions, add preflight ordering and strict output parsing tests, and run the actual CLI parser/cleanup helpers without cloud mutation. CI builds the immutable CLI source. Run checker/docs and relevant workflow checks; real cloud evidence is scoped separately from Docker image qualification.

## Acceptance criteria

- Compatible list/create/kill and strict parsing regressions pass.
- Mismatched CLI stops before deploy/cleanup.
- Existing ownership/recovery and SDK/image controller tests pass.
- Actual parser integration and repository CI pass.
- Bilingual contributor instructions and dated evidence included; PR merged.

## Evidence

[Verification](../../../evidence/verify/2026-10-23-command-recovery-review.md). Issue: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/192.

## Implementation

The scoped code and design corrections are implemented and locally verified. Reporting remains design-only. Final-head repository CI and merge confirmation are recorded in the linked PR; this pre-merge evidence snapshot does not claim that pending checks or publication already completed.
