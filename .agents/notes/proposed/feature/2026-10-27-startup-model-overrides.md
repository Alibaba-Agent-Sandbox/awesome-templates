# Decision: Accept explicit startup model settings through public launch

Status: proposed

## Problem
Qwen endpoint/model, DeepSeek endpoint/model and Hermes provider were nonempty
manifest defaults. The published launch resolver preserves such values over host
exports, forcing source edits for ordinary custom-service configuration.

## Decision
Declare those slots empty and preserve their previous vendor fallback values in
runtime. Qwen fills its child environment with the prior base/model when omitted;
Hermes setup and execution agree on the omitted/blank OpenRouter provider.
Update both README languages, design and versions. Keys remain environment-only.

## API Design
Existing names, typed command arguments and vendor defaults are preserved. Explicit
startup exports now select the configured service without modifying public source.
Per-call model/provider arguments retain precedence. Running instances are unchanged
by later host exports; create a new instance to apply startup changes.

## Alternatives considered
Requiring local YAML edits or only per-call overrides leaves newcomer setup harder
and read-only configuration inspection inconsistent. No endpoint/key reassignment
or undocumented credential conversion is introduced.

## Dependencies
Fixes https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/261;
refs https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/244.
CLI0.5.7 uses declared-default then host-value precedence. Credentials must be for
the selected service and protocol; compatible-model use cannot certify vendor accounts.

## Test Strategy
Actual existing command regressions plus new blank/default/explicit configuration
cases, old-source negative control, specification and bilingual document checks.
Then launch the pinned public source using actual explicit model settings; require
native model work, exact artifacts, all exposed methods, literal CLI/SDK/HTTP,
second configured model and independently confirmed owned cleanup before review.

## Acceptance criteria
Local checks and current-head CI pass; actual modified-source provider receipts
must establish business behavior. Articles and Registry review remain separate.
Do not remove Beta from local regressions alone or close the full50-template Issue.
