# Decision: Document the actual managed interpreter and preserve its failing boundary

Status: proposed

## Problem
The managed interpreter README only exposed independent process execution. Real
persistent code/context APIs and chart export needed a useful example. Actual
error-side-effect execution revealed an unresolved managed runtime defect.

## Decision
Document the separate public AsyncSandbox interpreter entry, explicit same-account
configuration, state/context lifecycle, callbacks and saved-file plotting. Supply
an unchanged executed expenses.py example. Describe the exception replay defect
and process alternative; keep full qualification pending. Preserve the successful
OpenCode OpenSandbox workflow as new dated evidence.

## API Design
No runtime, manifest, dependency or public API changes. The example uses explicit
api_key/api_url/domain options, finite lifetime, checked execution.error, downloaded
JSON/PNG and finally deletion. ProviderSandbox.run_code remains unsupported here.

## Alternatives considered
Calling a process-only check full interpreter acceptance, assuming inline IPython
plotting, or accepting only successful code would hide actual behavior. Do not
patch or claim ownership of the provider-managed image from this repository.

## Dependencies
Refs https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/244 and
https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/251;
https://github.com/Alibaba-Agent-Sandbox/blogs/issues/16 tracks the practical post.

## Test Strategy
Run literal CLI and complete existing SDK examples, persistent state and isolated
contexts, real pandas/PNG processing, callbacks, controlled nonzero/error paths,
and the complete downloadable example. Decode downloaded PNG independently and
verify own instances absent. Retain both failed assertions and replay reproduction.

## Acceptance criteria
Bilingual docs, runnable example, links and records pass. Native error replay stays
visible as FAIL and prevents full provider qualification until its owner fixes it.
The normal data/plot case can be published without claiming all interpreter paths
passed. Overall catalog acceptance remains incomplete.
