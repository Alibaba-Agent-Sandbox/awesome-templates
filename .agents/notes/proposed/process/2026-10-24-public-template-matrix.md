# Complete public-package template launch evidence

Status: proposed

## Problem

Earlier image and guest-bridge checks could not prove that a developer could launch
all default source recipes through the installed public CLI. They also did not
exercise the website’s remote Git retrieval commands. A maintenance label must not
be presented as a substitute for either kind of evidence.

## Decision

Preserve each real run as a dated, immutable receipt. Validate all 46 source templates
through the existing CLI launch path on Express and default direct OpenSandbox,
using published CLI and Python distributions, independent CLI/Python/host HTTP smoke
calls, runtime source identity and independently confirmed owned-resource cleanup.
Keep the separate public Git journeys and public-install pilot alongside the full
matrix. The repository PR checklist now asks for concrete entry-point results and
maintenance ownership, removing its stale status-to-test-level coupling.

## API Design

No product API, schema, template runtime or support state changes. Existing reports
retain their original fields and bytes; the overview explains fixture references,
actual install receipts, unknown unfixed Git commits and host versus guest versions.

## Alternatives considered

A source build of the packages would not validate their public installation. A
runner-side Dockerfile rewrite would bypass the behavior under test. Automatically
promoting catalog status after a successful run would conflate maintenance with
point-in-time evidence. Repeating 92 cases for documentation-only commits adds no
runtime coverage; preserve the exact tested tree instead.

## Dependencies

- [CLI release source](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/commit/413d575a688bd6f870c42c711d11346d176e0f38), public npm 0.4.16.
- [Python release source](https://github.com/Alibaba-Agent-Sandbox/python-sdk/commit/1b235830bc4a8cbec275b530bf2dc2869e8d0c4b), public PyPI client/server 0.3.1a5 on the host.
- [Provider fixture](https://github.com/Alibaba-Agent-Sandbox/awesome-providers/commit/e18489155697dcf2ee55a47b403396069d6cfa20).
- [Owner acceptance Issue](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/203).

## Test Strategy

Compare the expected 46×2 set with workflow jobs and original sanitized artifacts;
check every report, installed version/source, manifest identity, smoke consumer list,
and cleanup counters. Preserve previous failures. Reconcile task-created GitHub
secret names after all cloud jobs finish and confirm their absence. Run local link
and record checks plus normal current-head CI before merging this evidence change.

## Acceptance criteria

- All 92 requested cases have successful workflow jobs and passing application/cleanup reports.
- Public installation and remote Git evidence scopes and unknowns are explicit.
- Historical failures remain available; no model/native interpreter/PTY/desktop claim is inferred.
- Only task-created secrets are deleted, with absence read back after the final run.
- The indexed owner evidence and this scoped PR pass review and required checks.
