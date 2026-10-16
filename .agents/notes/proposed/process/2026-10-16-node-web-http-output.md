# Decision: Make Node Web HTTP assertions visible to strict acceptance counters

Status: proposed

## Problem

The actual-image smoke passed SDK/HTTP/CLI, but the full HTTP script returned0
with PASS0/FAIL0/SKIP0 as interpreted by its external owner. The script has a valid
entrypoint; its unbracketed PASS labels do not match the strict `[PASS]` counter.
Refs [Issue29](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/29).

## Decision

Normalize only node-web check() output to bracketed PASS/FAIL. Keep assertion
exceptions and positive-pass-count acceptance strict. A review of all17 current
product templates found this sole unbracketed formatter. No shared-parser legacy
allowance or product/runtime change is needed. Preserve prior rejected evidence.

## API Design

No named command, parameter, HTTP endpoint, image pin or template metadata changes.
The host HTTP acceptance script emits `[PASS] label` for a passed assertion and
`[FAIL] label` before raising on a failed assertion. Its exit status remains
authoritative together with zero failures and positive recognized checks.

## Alternatives considered

Accepting exit0 without recognized assertions hides accidentally empty scripts.
Widening all counters is unnecessary when the other16 templates conform. Treating
the rejected zero-count run as prior acceptance would rewrite its actual gate.

## Dependencies

Existing Node/npm, paired server SDK, httpx and pytest. The real regression uses
the existing local runner, an owned temporary npm cache and unchanged original
HOME. No new dependency, download or shared store mutation is introduced.

## Test Strategy

First run a new actual server/Node/npm HTTP regression against the old formatter:
exit0 but strict counts0 causes a genuine failing test. After the narrow fix,
all60 checks must be recognized; a real HTTP503 fixture must produce nonzero and
a countable FAIL. New actual-image HTTP acceptance is separate from these local
tests. Destroy only owned sandbox/template resources; borrowed image/registry
lifecycle remains with its original batch owner.

## Acceptance criteria

- Exact red→green full HTTP/counter reproduction and explicit failure control.
- No product/runtime/config change or weakened common gate.
- New image HTTP evidence with precise original-image/new-controller provenance.
- Bilingual docs, verification record, latest normal CI and draft PR.
- Issue29/canonical deploy/formal provider status remain open until actually done.
