# Decision: Independently verify Qwen coding through the restricted Agents API

Status: proposed

## Problem

The existing Agents CLI HTTP smoke truthfully rejects required model acceptance:
it has no independent view of files or test execution. This is an implementation
gap, not a missing native-model-key prerequisite. Refs
[Issue25](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/25).

## Decision

Add a self-contained SDK controller owning its disposable Express sandbox. Keep
the installed product runtime and HTTP policy unchanged. Use provider-native
commands solely for project setup and independent evaluation, and real HTTP
session/event/reconnect/items operations for the Qwen model turn. Selected model
env reaches a new9010 process before startup; original HOME remains intact.

## API Design

`e2e_sdk.py --template ID --journal PRIVATE --report RESULT [--model MODEL]
[--turn-timeout 30..600]` uses host OPENAI_API_KEY/OPENAI_BASE_URL only for the
new target server process. No cloud/GitHub key is forwarded. Public output is a
sanitized PASS/FAIL/checks report; private identifiers stay in a mode0600 atomic
recovery journal. The original server's explicit state directory is read only
through the management channel to observe one completed turn. This internal
fixed-version diagnostic does not establish coding correctness by itself.

## Alternatives considered

Reopening HTTP files/process routes changes the product contract. Accepting an
external success receipt or arbitrary verifier command makes the required-model
gate spoofable. The HTTP-only smoke therefore continues to fail required model
requests and links the self-contained controller. A Qwen pass cannot stand in
for Codex; its Responses compatibility remains a separate branch.

## Dependencies

Original installed Codex0.162.1/Qwen0.23.0, Node24.16.0, server e2cb27e fixed source,
the paired Python SDK and existing provider-native channel. Model calls require
a tool-capable OpenAI-compatible endpoint; Qwen supports the already authorized
qwen3.8-flash configuration. No extra host runtime or global dependency is added.

## Test Strategy

Exact initial failure, actual changed source, frozen original test bytes, exact
artifact/report, complete unittest modules and six held-out cases. Isolated
source compilation, BaseException handling and fresh post-agent ACK reject
skip/early exit0/pycache false greens. Negative controls cover altered tests,
missing/wrong artifacts, noncompleted state, permission/readback failure and
strictly scoped cleanup. Local synthetic controls are separate from real image
and model evidence. Full_access is disclosed; this is not hostile-code isolation.

## Acceptance criteria

- Unchanged product policy; no HTTP files/shell/process route or verifier hook.
- Only selected target env; original HOME and shared host stores preserved.
- Real Qwen turn plus independent complete source/tests/artifact gates.
- Own Sandbox create/kill and paginated absence; failed cleanup cannot pass.
- Bilingual docs and exact local/image/cloud evidence, preserving prior failures.
- Draft PR; Issue25, canonical deploy, Codex and formal verification remain open.

## Verification checkpoint

Root independently reviewed frozen1f975ff and reran41 regressions. Actual CI
image/Qwen SDK coding then passed, with8 owned cleanup flags and5 independent
read-only readbacks. [Evidence](../../../evidence/verify/2026-10-16-agents-cli-qwen-l3.md).
This decision remains proposed because the PR is draft and canonical/Codex gates
are not completed. Refs [PR101](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/101).
