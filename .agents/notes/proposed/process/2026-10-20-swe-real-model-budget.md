# Decision: bounded SWE operating budget and optional native tool calls

Status: proposed

## Problem

[Issue35](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/35) requires actual mini CLI submission and independent real-instance evaluation. The earlier strict image run failed before submission under the controller's implicit12-step budget. A separately owned actual Express diagnostic submitted after25 calls and passed all60 original test identities with zero failures/errors/skips.

## Decision

Request the already supported maximum30 steps and600-second command budget in the standalone controller and bilingual examples. Preserve API defaults12/300, all baseline/original-test identity/artifact/cleanup gates and the explicit non-official benchmark scope. The budget-only repeat still failed before submission. Version1.1.0 adds opt-in official native function calls while preserving legacy text defaults; a fresh runtime image is required. No assertion or scoring gate is relaxed.

## API Design

The controller sends max_steps30 and command_timeout from bounded E2E_COMMAND_TIMEOUT (default600,30–900), with request timeout60 seconds greater. Existing shell permission and target key checks stay unchanged. SWE_MODEL_PROTOCOL=text (default) selects litellm_textbased/default.yaml; toolcall selects litellm/mini.yaml. Invalid modes refuse before mutation. The setup flag native_tool_calls is required by the strict controller. The new runtime contract version is1.1.0; Docker dependency pins remain unchanged.

## Alternatives considered

Do not count the diagnostic as canonical acceptance or replace the model's source edit with an operator patch. Do not remove the failing baseline, fresh evaluator or patch/report retrieval. The supported API already exposes the required budget, so changing the text default would break existing callers. Optional native-tool selection follows the actual installed2.4.6 upstream implementation; its fixture demonstrates real CLI behavior without making a model/provider claim.

## Dependencies

Fresh SWE1.1.0 image from the published reviewed source (old1.0.1 artifact12242554950 is diagnostic only), unchanged environment/process/instance inputs, mini2.4.6, Python3.11.10 evaluation venv, compatible qwen3.8-flash configuration and actual SDK-created owned sandbox. Source dependency PR135; SDK-route dependency PR138.

## Test Strategy

Demonstrate that the old controller omits the adequate budget. Verify request budget and cleanup through synthetic HTTP only, retain all existing false-green/missing-key/identity regressions, then run a deterministic native HTTP tool-call fixture against the actual installed mini (failed before correction, passed after). Rebuild1.1.0 and run the exact changed controller against its new image with actual model and independent owned cleanup.

## Acceptance criteria

- The configured genuine mini agent submits within the bounded supported budget.
- All60 exact original test identities pass in a fresh evaluator; patch and report independently retrieved; no skips or official score claim.
- Exact controller/image hashes and actual SDK creation recorded only after independent owned cleanup.
- Current-head CI, bilingual operations/records and normal merge complete delivery; diagnostic success alone is insufficient.
