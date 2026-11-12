# Decision: Preserve independent resources and reserve Worker bootstrap inputs

Status: proposed

## Problem

The first v1 draft forced every Sandbox plus native Devs project to select the Agents API
business coordinator. That imposed a Managed implementation limit on otherwise meaningful
independent resources. Newly connected Worker environment bootstrap keys could also be
silently overridden by user native role properties.

## Decision

Allow independent `sandbox` and `deployment` declarations without `application`. Preserve both
in normalization and private compilation. This does not implement their joint execution:
consumers must reject unsupported mixed deployment before preparation or cloud side effects.
Keep the Agents API role and lifecycle constraints conditional on its explicit business type.
Reserve `ABX_MANAGED_SANDBOX_ENV_JSON` and `ABX_MANAGED_SANDBOX_ENV_FILE` in Managed native role
properties, matching the Worker-only SDK environment channel.

## Alternatives considered

Reject all mixed declarations in the resource schema: simpler but incorrectly makes one
business coordinator mandatory. Automatically orchestrate mixed resources: creates implicit
coupling and an unsupported execution promise. Allow bootstrap overwrites: risks a deployment
whose effective private instance environment disagrees with the reviewed inputs.

## Dependencies

Tracker: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/309.
CLI consumers need the explicit pre-effect unsupported guard. SDK and CLI source locks must
advance to this producer commit. Full migration and cloud acceptance remain separate.

## Test Strategy

Run actual AJV and Python jsonschema against shared positive and negative vectors, compare
complete outputs, assert both independent resource blocks survive compilation, and reject
both protected native Worker keys. Existing Managed negative vectors remain active.

## Risks and Limitations

Static admission does not make arbitrary combinations executable. No native expression is
evaluated by the pure contract. This incremental producer change is locally verified only.

## Rollback Plan

Revert this isolated contract change with coordinated consumer locks. Do not rewrite existing
receipts or claim unsupported combined execution became accepted.
