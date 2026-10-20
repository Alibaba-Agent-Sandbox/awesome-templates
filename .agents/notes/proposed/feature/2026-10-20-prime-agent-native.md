# Decision: original stable Prime Agent native Rust CLI

Status: proposed. Refs https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/69.

## Problem

Issue69 surveyed a nightly-only/Anthropic-only Prime Agent runtime. Current official stable v0.10.0 and its native Rust CLI now provide an immutable Linuxx64 release plus original Python RLM runtime. This must be verified as the actual product, not replaced by another agent.

## Decision

Implement the unchanged official native0.10.0 binary and complete original release sidecars/notices, an isolated fully hash-locked Python kernel and explicit compatible-model provider. Model-generated code runs only on a fresh owned disposable cloud target. Use original supported private agent-dir/kernel-Python/model/settings controls, disable discovery/telemetry/subagent recursion for this bounded slice and clean all owned detached native/kernel processes.

## API Design

Planned scalar version/setup and prime_agent(prompt,cwd,command_timeout) with fixed native path/hash, private0700 HOME/settings, anonymous stdin, explicit model/key/base validation,256KiB per-stream bounds and exact owned cleanup. Final parameters/native terminal JSON checks must be documented and independently tested. No vendor subscription, daemon service, recursive-agent/research benchmark or other-provider acceptance is claimed.

## Alternatives considered

Floating install scripts/nightly aliases are unnecessary after official stable release. A native version/help pass is identity evidence only. No community agent or synthetic chat implementation can establish genuine Prime Agent coding. Original Python runtime can be supplied through its supported fixed kernel interpreter rather than floating first-run package bootstrap.

## Dependencies

Official stable releasev0.10.0 published2026-10-09; annotated tag resolves public source763094e1b6a7c17450ee8399b06cda1853847ca5. Official Linuxx64 archive21556959bytes/SHA256c16bd2af5e77b53f49b914a44742c4cf6a67c5ed5000041430b78dbd4c3bcbec; original executable61057216bytes/SHA256546e71921bb0fa278c9d50dd8c61a27b835413552cb08a9359d0e320848e39d6. Both archive and executable digests are published in the official release manifest; unlike controller-measured digests, that provenance is explicit. Full108-member release expands63849622bytes and includes MIT license/PHOTON third-party license/runtime source/model catalog. Python runtime package source version0.1.0 is distinct from CLI0.10.0.

## Test Strategy

Read-only original native --version/--help with a fresh private HOME/minimal environment; no model key or generated-code execution. Then authored validation/config/credential/kernel-env/ownership/terminal JSON regressions, actual image pin/kernel checks and canonical SDK-created Express steps/fullHTTP. Before a real key, prove fixed native custom routing on a synthetic-only local cloud fixture. Genuine original CLI/native ipython-named CPython REPL then edits seeded existing source, preserves original test bytes, creates report/fresh nonce artifact and passes complete original plus independent held-out post-return tests. Independently verify native/kernel/private/listener/project/sandbox/template/cache absence; preserve every failure/skip.

## Acceptance criteria

- Original release/binary/sidecar identity, licenses and exact native configuration are proven; no floating dependency bootstrap or substituted agent.
- Authored guards/current image/steps/SDK/HTTP and genuine native coding/artifact/unchanged-test/held-out checks pass on Express with independent owned cleanup.
- Bilingual docs/design/catalog/records agree; qualification only follows actual current receipts and required latest-head CI/review/normal merge.
