# Publish compatible installation instructions and durable matrix evidence

Status: Proposed

## Problem

The specification 5 migration intentionally retained source-candidate installation instructions while consumers were being released. Its committed checkpoint predates completion of the full OpenSandbox matrix, whose Actions artifacts need a durable repository copy.

## Decision

After compatible public packages and the migration are available, recommend CLI 0.5.0+ and explicitly pinned Python client 0.4.0a1. Update both usage languages, shared Python installation, four managed quick starts and current indexes. Preserve all 46 sanitized receipts and the independent verification summary in a new dated directory; retain older evidence unchanged.

## API Design

No runtime or schema change. Installation uses `npm install -g @agent-sandbox/cli@0.5.0 --registry=https://registry.npmjs.org` and `python3 -m pip install --index-url https://pypi.org/simple 'agent-sandbox-client==0.4.0a1'`. Templates continue to launch through one command. Existing source-matrix receipts do not establish published-package or managed-launch acceptance.

## Alternatives considered

Keeping temporary source installation indefinitely obscures the supported release. Rewriting the earlier pending record loses its historical timing. Repeating 46 cloud experiments for documentation would add no evidence about changed runtime behavior.

## Dependencies

[Template migration PR](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/213), [CLI PR](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/pull/152), [Python SDK PR](https://github.com/Alibaba-Agent-Sandbox/python-sdk/pull/108), and publicly retrievable compatible packages. Refs https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/212.

## Test Strategy

Run documentation links, checker/catalog gates required by repository instructions, whitespace checks and the offline receipt verifier. Confirm copied JSON bytes equal the downloaded artifacts. Validate public installation separately once release availability is confirmed; do not reclassify source experiments as registry installations.

## Acceptance criteria

The migration and compatible packages are available, installation examples resolve, all documentation checks pass, durable receipts reproduce the 46/73/219 results with exact hashes and cleanup, and the scoped follow-up PR merges through normal gates. Until then this remains a prepared documentation follow-up.
