# Decision: Read current resource paths in template protocol regressions

Status: proposed

## Problem

The latest actual local-e2e job stops in SWE's existing protocol regression because it still
reads retired root env from template.yaml. The later agents-cli canonical-startup regression
likewise reads retired root start_cmd. They are test consumers missed by the resource migration,
not evidence that the published a7 server, CLI source or host dependencies failed.

## Decision

Use the owner's shared bounded Core source reader in these two existing tests. Read
sandbox.instance.envs for SWE's shipped protocol and sandbox.start for agents-cli's shipped
startup. Remove only their unused PyYAML imports. Keep all original budget, cleanup, actual
HTTP, authentication/allowlist and fixture isolation assertions, both startup forms, original
business runtime files and the existing CI invocation.

## Alternatives considered

Restore retired root fields or accept old aliases: pollutes the new public contract. Skip
canonical-startup or lower protocol assertions: hides actual behavior. Upgrade SDK or change
runtime pins: no log evidence supports that intervention. Copy a new YAML resolver into tests:
duplicates the canonical source policy. These alternatives are rejected.

## Dependencies

Actual failure: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/43290753694/job/131436058740
at6f7aee8844a54e37ae251cf4020d77b8ce03a63b. Canonical reader is ef695803cb78bf82b8473195fcb37b3e6357a363.
Tracker: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/309.

## Test Strategy

Retain the original local4-failed/19-passed control and actual Actions failure identity/hash.
Install the exact published client/server0.4.0a7 and CI test/spec dependencies in a fresh
Python3.13 environment; run the same23 regressions and both complete related workflow groups.
Check dependency consistency, scoped lint, documentation links and whitespace. Latest remote
local-e2e must still execute its complete unchanged template suite.

## Risks and Limitations

Tests run from the repository root as python -m pytest, so scripts is available as its existing
namespace package. Shared source reading retains unresolved expressions and evaluates no local
configuration. These synthetic/local HTTP regressions are not vendor/model/cloud acceptance.
A focused local pass cannot establish the remaining remote workflow steps passed.

## Rollback Plan

Revert the two test-reader changes and retain the failure/control evidence. Do not weaken
runtime behavior assertions or add compatibility fields to make old test access succeed.
