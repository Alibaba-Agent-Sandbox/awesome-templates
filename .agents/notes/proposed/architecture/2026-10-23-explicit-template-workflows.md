# Explicit template workflows
Status: proposed

## Problem

A template-wide code token conflated a provided Python service with a provider interpreter, and historical provider labels looked like current proof.

## Decision

Require specification 4 with explicit services, default workflow, exact operations and binding. Migrate all current source/application manifests and catalog schema 2 without a legacy parser. Preserve application topology and old receipts as history. Vendor exact shared contracts at commit b8d06847780448193f7d529c59c40b5ba9cc6b8d. Add an explicitly selected portable python-hello recipe; never rewrite the existing Express recipe.

## API Design

Application HTTP, exec and interpreter paths are distinct. Only the selected workflow can require an interpreter operation. Unknown runtime prerequisites do not mean the platform lacks an API. Beta maturity and current workflow evidence remain independent. No old schema or coarse code compatibility aliases are accepted.

## Alternatives considered

Keeping broad code capability gates or silently replacing platform build instructions would continue to misrepresent application support and source identity.

## Dependencies

- [Owner Issue](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/194)
- [Shared contract](https://github.com/Alibaba-Agent-Sandbox/python-sdk/blob/b8d06847780448193f7d529c59c40b5ba9cc6b8d/contracts/workflow-v1.json)
- [CLI workflow implementation](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox) (consumer dependency; final reviewed revision must be pinned before native integration acceptance).

## Test Strategy

Validate strict manifests and operation boundaries, unchanged source build recipes, explicit profile selection and conservative historical evidence handling. Native workflow verification must use exact implementation revisions and independent owned-resource cleanup.

## Acceptance criteria

Current manifests and consumers agree on the new contract; relevant regression and current-head CI gates pass; native acceptance remains explicitly incomplete until exercised. Merge only after required review and checks.
