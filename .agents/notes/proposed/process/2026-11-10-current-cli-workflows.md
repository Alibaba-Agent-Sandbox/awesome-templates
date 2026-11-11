# Current CLI workflows

## Problem

The unified CLI removes duplicate template/app lifecycle entry points. Current
recipes and their executable harness still call removed commands. Tracked with
https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/302 and
https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues/244.

## Decision

Document one deploy entry, named lifecycle management and sandbox runtime commands.
Use template init for obtaining source and build/publish for author work. Show
source installation explicitly because published CLI 0.5.10 lacks this surface.
Keep historical verification records and fixed-release walkthroughs unchanged.

## API Design

Current guides use deploy, list/status/logs/delete/recover, sandbox operations,
and template init/build/publish. The managed recipe deploys directly with bindings;
optional reusable builds remain borrowed by a deployment. Native provider template
cleanup uses provider run template.delete/list with structured input and --yes for
deletion. Public deployment identity fields remain required by the harness.

## Alternatives considered

Keeping old examples would document commands removed from the current source.
Inventing compatibility aliases would undo the approved single-surface design.
Revalidating every template in the cloud solely for prose changes would expand the
request; rewriting old qualification receipts would create false evidence.

## Dependencies

The CLI source implementation must land before these instructions are advertised
as released. Registry and website consume these current docs. Existing source
identity rules include README bytes, so changed templates require independent
qualification against their new source identity. No identity algorithm or receipt
is changed to preserve a badge.

## Test Strategy

Run specification, document, generated-source and catalog gates. Exercise the real
CLI parser with isolated empty configuration, and the local lifecycle harness
regressions without cloud mutation. Parent coordination owns actual cloud checks.

## Acceptance criteria

Current bilingual recipes have a coherent source installation and deploy/cleanup
path; executable harness commands match that surface; historical evidence remains
intact. Each local result and unexecuted cloud/publication step is reported honestly.

Active image/steps and managed-template harnesses also migrate to the same public
commands. The image/steps helper only shapes the existing native CRUD JSON call;
it does not add a build engine. Cleanup first exercises named public delete
(recover first after a failed deployment), then independently checks Sandbox
absence and performs exact-owned fallback cleanup. A failed public cleanup stays
failed even if fallback eventually removes the resources.
