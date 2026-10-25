# Use one current application token in template verification

Status: proposed

## Problem

Current controllers still read retired E2E_TOKEN/E2E_SERVER_TOKEN aliases, and the host helper injects the same application token under three names. Some controllers consequently treat the application token as a gateway access token. Current managed interpreter examples also contain a retired OPEN_SANDBOX_API_KEY fallback.

## Decision

Use only ABX_SERVER_TOKEN for application Bearer authentication. Pass provider gateway authentication through the existing validated E2E_GATEWAY_HEADERS_JSON mapping. Remove retired aliases and their precedence tests; do not add compatibility handling. Preserve genuinely distinct native fixtures and OpenClaw gateway credentials. Use ABX_OPENSANDBOX_API_KEY in the current managed examples.

## API Design

No new user option, runtime command or manifest service. This changes the development verification environment and current example names, not the provider's actual upstream ConnectionConfig.api_key parameter. Historical evidence remains immutable.

## Alternatives considered

Maintaining all aliases duplicates configuration and allows callers to confuse application and gateway credentials. The user explicitly requests the current interfaces only, so no migration fallback is needed.

## Dependencies

Existing public Python application client and provider header mapping. Refs https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/215 and https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/216. The client's independent token-header contract remains owned by https://github.com/Alibaba-Agent-Sandbox/python-sdk.

## Test Strategy

Real local HTTP checks assert separate application Bearer and provider access-token values. Child-controller tests verify no operator token aliases are inherited. Existing command/controller regressions, template/document checks and current-head CI remain required. Real public cloud reruns must execute the final controllers after publication.

## Acceptance criteria

- No current controller reads retired token aliases; negative regressions may name them to prove exclusion.
- Current docs and both managed example languages use the same names.
- Required local/current-head CI pass; actual reruns retain exact inputs, failures/skips and independently confirmed cleanup.
