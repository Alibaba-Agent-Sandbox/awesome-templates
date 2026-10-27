# Decision: Exercise Polyglot public command discovery

Status: proposed

## Problem
The native controller checks health and both actual compiler methods but omits
GET /commands, although the reviewed public-method inventory includes discovery.
A method in an inventory is not evidence that it was actually called.

## Decision
Request actual command discovery before compiler checks and require exactly the
two registered toolchain methods. Retain all real version/compile/output/cleanup
assertions. Preserve original successful business work as its actual narrower
scope and obtain fresh complete Express/OpenSandbox evidence.

## API Design
No runtime, dependency, named command, README program or API changes. Only the
external native acceptance controller gains an observable discovery assertion.
Current folder identity changes, so old receipts cannot qualify the new source.

## Alternatives considered
Inferring discovery from a successful named command or silently copying the
unexecuted method into a passed inventory would not satisfy complete API use.

## Dependencies
Refs https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/287 and
https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/244.
Registry PR86 must review the new source/provider receipts before public promotion;
practical case source belongs to blogs PR31. No native model account is needed.

## Test Strategy
Show the original controller passes an HTTP fixture without discovery and the new
controller rejects missing/incomplete discovery while accepting a complete fixture.
Those fixture compilers are synthetic and never count as native toolchain proof.
Run existing process tests, specification/local conformance, real two-provider
native compilers and literal CLI/full SDK/direct HTTP tasks with independent cleanup.

## Acceptance criteria
Both actual provider workflows, all four public endpoints, independent owned
cleanup, source/current-head gates, reviewed Registry identities and public readback
pass. Preserve original evidence and never infer full50-template completion.
