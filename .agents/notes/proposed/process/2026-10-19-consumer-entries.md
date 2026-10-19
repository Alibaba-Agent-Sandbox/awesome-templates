# Decision: Keep consumer examples valid across client entries

Status: proposed

## Problem
Consumer examples await root Sandbox, which becomes the standard synchronous client.
Native server/provider calls need an explicit native import. CLI builds also differ
in create/exec/kill parsing even when their package version strings are equal.

## Decision
Use agent_sandbox.api.sandbox.Sandbox for native async/server/provider examples;
it exists on accepted main and the standard candidate. Keep current source-install
pins and working native CLI syntax. Where standard Express is relevant, describe
the installed-help distinction and positional --detach create/kill without --yes.
No package release, runtime source, template badge or public capability changes.

## API Design
N/A — documentation selects existing public entries; no API implementation changes.

## Alternatives considered
Updating every example to the new root breaks native named commands/providers.
Publishing only future positional CLI syntax breaks existing main installations.
Version-number thresholds are unreliable while both builds share the same version.

## Dependencies
https://github.com/Alibaba-Agent-Sandbox/python-sdk/pull/47
https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/pull/40
Blog source belongs to https://github.com/Alibaba-Agent-Sandbox/blogs; website
snapshots are refreshed from that owner. Registry aggregates source documents
without a shared-UI/catalog contract change.

## Test Strategy
Check both native imports and coroutine shape against accepted and candidate
clients. Run owner documentation/build/record gates, inspect bilingual examples
and confirm runtime sources and evidence badges are unchanged.

## Acceptance criteria
Native examples remain valid on both entries; CLI choice matches actual help.
Bilingual content, owner records and required current-head CI/review pass.

## Evidence
[Verification](../../../evidence/verify/2026-10-19-consumer-entries.md).
