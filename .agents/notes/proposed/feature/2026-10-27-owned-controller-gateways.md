# Decision: bind model controllers to the created sandbox and resolved gateway

Status: proposed

## Problem
Eight controllers reject every loopback hostname even when the CLI just created
an owned Docker sandbox and resolved its official OpenSandbox gateway. Actual
Copilot proof stops before the model task:8 PASS/1 FAIL, exact owned cleanup.

## Decision
After creation/connect/runtime verification, require connected ID equals the CLI
launch and supply that ID plus exact SDK-resolved app URL to the controller.
Never inherit these markers from operator environment. A local-target allowance
requires both the explicit real-usage ownership flag and the exact bound URL/ID;
proxy paths containing a sandbox ID must match it. Preserve all model/source-edit/
independent-test/documentation conditions. A checked generator owns the identical
small policy function in all eight standalone controllers; no new image imports.

## API Design
No public template command, runtime, Dockerfile or manifest change. Add optional
internal owned_sandbox_id to the controller driver; default is unbound. Ordinary
standalone local targets still reject; existing nonlocal target opt-in is retained.
No hostname alias, address rewrite, arbitrary inherited credential or skip flag.

## Alternatives considered
Changing a hostname to evade a local-address check would hide the ownership issue.
A generic real-usage flag without endpoint binding is insufficient. Keeping the
blanket guard prevents real approved Docker verification despite actual isolation.

## Dependencies
Refs https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/282 and
https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/244.
New source identities include changed verification files, so all eight require
fresh Express/OpenSandbox actual workflows and Registry review before acceptance.
Original runtime/manifests remain unchanged; historical receipts stay preserved.

## Test Strategy
Original controllers reject a correctly owned gateway:8 FAIL/40 PASS before fix.
After fix,130 tests plus6 subtests PASS, including actual original controller
branches for missing/wrong URL/wrong ID/no ownership/valid owned/existing remote,
operator marker isolation and generator drift. Spec39, all-template checker and
224-document links pass. Real current-source eight-template dual-provider method,
model/business/documentation runs and exact cleanup still required.

## Acceptance criteria
No guard bypass or model/test weakening; exact created-target binding, no operator
marker inheritance, complete original actual workflows, final-head CI/review and
current-source Registry qualification. Full50 request remains incomplete.
