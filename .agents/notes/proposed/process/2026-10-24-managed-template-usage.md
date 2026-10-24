# Managed template usage and default execution

Status: proposed

## Problem

The managed READMEs mixed usage with obsolete CLI/internal SDK examples, local
credential availability and long acceptance-report prose. The OpenSandbox interpreter
entry selected an unimplemented unified interpreter operation by default, while its
upstream SDK example omitted the explicit service entrypoint now required by the
provider. Tracking: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/206 .

## Decision

Keep the existing managed schema and fourteen README headings. Replace report prose
with usable bilingual instructions, actual capability boundaries and dated links.
Use public ProviderSandbox. Select the implemented managed exec default for
OpenSandbox, and document upstream native sessions separately with an explicit
entrypoint. E2B desktop retains a concise statement that no live run is recorded.

## API Design

No provider or SDK API changes. OpenSandbox's catalog workflow uses the existing
exec.run operation. The existing provider_options.entrypoint starts the upstream
interpreter; it does not implement ProviderSandbox.run_code for this provider.

## Alternatives considered

Keeping the blocked default behind explanatory prose would leave an unusable entry.
Treating upstream native SDK success as unified interpreter support would be false.
Adding another capability/status schema is unnecessary.

## Dependencies

Use CLI 0.4.16, public paired Python packages 0.3.1a5 and provider source
6eec4e76bb955a2a8cd89f725e66bb7887d6c819. The existing native Docker fixture retains
its upstream server/native SDK source and lockfiles, with the current argv-capable
execd pinned by digest independently of the interpreter image. Historical JSON is immutable.

## Test Strategy

Run managed/schema/document checks and syntax-check all Python examples. Reuse the
existing isolated native Docker job: first create a distinct default instance and
execute Python, then create a separate explicit-entrypoint instance and exercise
upstream Python calculation, context persistence/isolation/error handling and cleanup.
Require independently confirmed deletion for both instances. Registry independently
regresses the actual catalog's generated default create/exec/kill commands.

## Acceptance criteria

Both languages are usable; the default catalog entry produces executable commands;
actual default and native SDK checks plus cleanup pass on exact recorded inputs;
all normal owner CI/review gates pass. No E2B desktop or unified interpreter pass is
inferred. The independent 46 × 2 source-template matrix continues unchanged.
