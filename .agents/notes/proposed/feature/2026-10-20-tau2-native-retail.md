# Decision: original Tau2 retail task execution and native replay

Status: proposed

## Problem

[Issue59](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/59)
requires genuine Tau2 operation inside CPU-only Express, with a useful named
command, SDK usage and actual cloud records. Package names or substitute tasks do
not establish original benchmark operation.

## Decision

Pin official v1.0.1 sourcefc0055dc4e0a316c3f83133267fbd6faaa770992 and the measured
official archive digest. Select original source and retail data only. Execute
original agent/user models and original evaluation, preserve a sanitized trajectory
and independently re-evaluate it with strict native replay in a keyless worker.
Explicitly reject non-retail and nonempty NL-judge tasks. Keep the slice wave2
and experimental until actual required acceptance passes.

## API Design

Four scalar commands: version, setup presence, retail run and artifact replay.
See [command reference](../../../../tau2-bench/README.md#command-reference).
Fixed isolated Python worker receives bounded anonymous stdin. Both participants
use explicit compatible model/base settings; key only enters private worker memory.
Own serialized process group, nonce, pidfd and private HOME cleanup apply to all
paths. Successful bounded artifacts remain caller-owned; failed partials are removed.

## Alternatives considered

A fabricated fixture score or replacement benchmark cannot fulfill the Issue.
Installing an unverified Tau2 distribution would lose source provenance. Full
voice/knowledge/data scope exceeds this task slice. NL judge evaluation adds a
separate model path and remains refused. Upgrading the upstream dependency graph
to satisfy a newer uv canonical lock check would change the pinned product.

## Dependencies

Original MIT source and data with retained notice; Apache2.0 wrapper. Frozen
upstream dependency export includes LiteLLM1.81.11, OpenAI2.20.0 and Pydantic2.12.4,
enforced through hash installation and pip check. Explicit approved model settings
for both native participants. Common immutable servere2cb27e. Modern uv `--locked`
export failed its freshness check; unchanged frozen export succeeded instead.

## Test Strategy

Authored validation, process, secret transport, path ownership, partial cleanup,
SDK request and independent evaluator regressions. Strict spec and bilingual link
checks. Actual image dependency/version checks, canonical native steps with SDK
creation and full HTTP checks. Actual original task0 must complete with reward1.0,
real agent/user/tools, independent artifact bytes/hash, keyless original strict
replay, fresh post-return acknowledgement and independently confirmed owned cleanup.
Local fixtures and skipped model checks do not establish native acceptance.

## Acceptance criteria

Complete bilingual docs, manifest, catalog, design and records; current required
checks pass. Actual image and Express/native SDK/model/replay receipts at exact
source with owned cleanup. Normal reviewed merge before Issue closure. Pending
cloud or required original-task behavior remains incomplete.

[Verification](../../../evidence/verify/2026-10-20-tau2-native-retail.md).
