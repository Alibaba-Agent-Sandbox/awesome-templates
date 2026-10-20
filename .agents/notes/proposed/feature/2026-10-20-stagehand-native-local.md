# Decision: native Stagehand4 local-browser slice

Status: proposed

## Problem

[Issue68](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/68) requires an actual useful Stagehand template with SDK, Express steps, bilingual docs, native acceptance and owned cleanup. A similarly named Python package or source import is insufficient. Official native4.3.0 differs from olderv3 examples and requires Node>=22.18.0.

## Decision

Install npm-integrity-locked official Node SDK4.3.0/Zod4.4.3 and SHA256-pinned Node24.16.0/Chromium1208. Use real upstream local browser/extension/act/extract with ephemeral per-call profile and new PNG. Use the supported ClientLLM callback for an explicit approved compatible structured Chat Completions endpoint, because pinned ModelConfig lacks a baseURL option. This transport maps provider requests only; no substitute browser agent is implemented.

## API Design

Four scalar commands: actual version, read-only setup booleans, offline native self-test, and one native act plus optional typed text extraction. Bound instructions/URL/inferences/outputs/deadline and serialize operations. Anonymous stdin memory conveys model settings to Node; browser inherits no model/cloud/GitHub credentials. Own process group, inherited nonce marker and pidfds clean descendants; private HOME/cache/profile removed and failed exclusive artifact deleted.

## Alternatives considered

Browserbase SaaS adds account requirements and does not prove local operation. Passing v3 baseURL to v4 strict schema fails. A chat-only wrapper, direct Playwright click or canned output cannot certify native Stagehand. No host execution of model-generated source, silent provider fallback or fabricated vendor key.

## Dependencies

Official Stagehand4.3.0 MIT tarball integrity verified, full npm lock; Zod4.4.3; official Node24.16.0 SHA256; Playwright1.58.0 Chromium145.0.7632.6; servere2cb27e. Explicit approved compatible base/key/model required for L3. Native operator SDKd4d93e8c and official native CLI0.4.1 for cloud acceptance; never send cloud credentials to Actions or model endpoint.

## Test Strategy

Authored local Node callback schema/text/image/status/size/call-budget tests and Python validation/concurrency/memfd/process timeout/overflow controls. Native self-test must launch real extension/browser and verify title/PNG. Actual L1 plus SDK-created canonical steps and independent owned cleanup. Real L3 unique cloud fixture requires genuine native semantic click, independently observed state, exact fresh receipt extraction, downloaded decoded PNG and own process/files/state absence. Mocks and model skips stay separate.

## Acceptance criteria

Complete source/catalog/design/English+Chinese docs/records; required local and latest-head CI pass. Actual pinned image build and current native Express steps/SDK/native browser/model receipts with exact provenance and independent cleanup; normal reviewed PR merge before Issue68closure. Pending or failed native compatibility remains explicit.

[Verification](../../../evidence/verify/2026-10-20-stagehand-native-local.md).

The existing bounded exact-asset steps profile now includes Stagehand with the same pinned Playwright1.58.0 non-headless-shell archive and temporary uv bootstrap. It preserves source installers, original hashes/wire/deadline/rootfs constraints, and independent private OSS ownership/cleanup; it does not relax limits or copy credentials into source.

Before native acceptance, template1.1.0 replaces the incompatible4.3.0 factory launch with owned Chrome preload plus native connect. The original4.3.0 factory silently ignored its accepted public extensionId option; a one-site pristine-SHA256-gated patch forwards it, preserving no-ID defaults. Worker independently requires the exact patched SDK source hash. This is an explicit documented patched distribution, not an unmodified upstream release, runtime provider fallback or simulated browser agent. A real pinned native SDK against an authored CDP endpoint must reproduce the original wrong first command and prove the forwarded-ID/default branches before native cloud rerun.
