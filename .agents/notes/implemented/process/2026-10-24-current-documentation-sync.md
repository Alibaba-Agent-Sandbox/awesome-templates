# Synchronize current documentation and engineering records

Status: implemented

## Problem

User-facing guidance and the engineering index still foreground older checkpoints after the October 24 delivery. Some merged decisions remain proposed; historical evidence must remain immutable.

## Decision

Update the installation recommendation to public CLI 0.4.17, explain its Qwen application timeout, use the public ProviderSandbox entry, and expose the 92-case matrix and separately scoped managed/Git checks from user documentation. Move the four merged October 24 decisions into implemented and repair their current index links. Add a concise changelog entry. Retain all dated evidence bytes, original tested versions and unchanged runtime inputs. Older proposed decisions are not promoted without reviewing their own acceptance criteria.

## API Design

Documentation only. No runtime, manifest, catalog, compatibility floor or package version changes; no new support-state taxonomy.

## Alternatives considered

Rewriting old receipts would destroy provenance. Copying the complete cross-repository report would duplicate ownership. Repeating cloud runs for navigation and prose changes would add cost without exercising changed runtime behavior.

## Dependencies

Baseline: `78c30fbbd186cb59c3a0f0abd9fdf85b10c84b35`. Requested by the maintainer as synchronization of recent changes into each repository's documentation and `.agents`.

- [Merged PR #204](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/204)
- [Merged PR #205](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/205)
- [Merged PR #207](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/207)
- [Merged PR #210](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/210)

- [CLI 0.4.17 delivery](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/pull/149)
- [Python 0.3.1a5 delivery](https://github.com/Alibaba-Agent-Sandbox/python-sdk/pull/103)

## Test Strategy

Check documentation links and changed record links, bilingual scope and public API examples; verify moved notes match their directories and original evidence files are unchanged. Run owning-repository applicable checks and require current-head CI before merge. No new cloud claim or cloud resources.

## Acceptance criteria

Current docs and the engineering index lead to recent delivered behavior and exact verification; historical receipts and runtime contracts are unchanged. Normal PR review and applicable CI gate publication.

## Evidence

[Documentation verification](../../../evidence/verify/2026-10-24-current-documentation-sync.md).
