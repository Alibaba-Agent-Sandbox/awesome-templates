# Decision: Make the default SWE recipe usable with native tool calls

Status: proposed

## Problem
Actual configured public SWE1.1.2 launch stopped before a model task: its nonempty
text protocol could not be overridden and failed the required native-tool gate.

## Decision
Ship toolcall as SWE1.2.0's manifest default. Keep text supported as an explicit
local template choice. Update bilingual migration/configuration and design.
Preserve actual failure and require a fresh original-instance evaluation.

## API Design
The protocol default changes; method signatures and explicit shell permission do
not. Tool-calling Chat Completions is required by the public default. Host exports
still cannot override nonempty manifest values. Users requiring legacy text must
set text in their own reviewed source copy.

## Alternatives considered
Weakening native-tool acceptance or silently rewriting the manifest during a run
would conceal the unusable public path. Changing only a host export has no effect.

## Dependencies
Refs https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/253 and
https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/244. Published
mini-swe-agent2.4.6, client/server0.4.0a6 and standalone CLI0.5.7 stay pinned.

## Test Strategy
The existing bounded-budget/cleanup regression now derives native setup from the
shipped manifest; it must reach the real-agent boundary and would fail with text.
Run command regressions, spec/docs checks, actual default Docker launch and native
agent repair with fresh60-test evaluator and independently confirmed cleanup.

## Acceptance criteria
Default source reaches the genuine model task and independent evaluator; methods,
docs, evidence and current-head CI pass. The full50-template request stays open.
