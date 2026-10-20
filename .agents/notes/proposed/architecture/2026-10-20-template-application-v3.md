# Single-file optional application contract

Status: proposed

## Problem

Developers need to describe either an Agent running inside a sandbox or an
external Agent using sandbox tools without introducing a second Agent manifest.
Template spec v2 describes sandbox launch only. Silently accepting new fields or
executing deployment hooks during installation/create would hide incompatibility
and cloud side effects.

## Decision

Add an opt-in v3 manifest schema with optional `application` inside `template.yaml`.
Keep v2 valid and unchanged. The checker recognizes v3 as supported, rejects an
application in v2, unknown explicit versions, unknown fields and illegal topology.
Malformed/duplicate YAML fails rather than bypassing claimed-spec checks.

Application deployment is explicit and owned by the CLI adapter. Hooks remain
bounded host/CI deployment extensions, never sandbox startup actions. Inline
Serverless Devs v3 configuration is extracted into a frozen generated deployment
artifact; advanced users may instead reference a project. Provider, application
deployment and runtime enforcement remain distinct contracts. No cloud execution
or existing runtime/image/catalog acceptance claim changes here.

## API Design

`schema/template-v3.schema.json` is the machine contract. It closes objects and
models external/local runtime, gateway, deployment, exclusive per-run sandbox,
state/binding references, budgets, and beforeApply/afterReady hooks. Both modes
require lifecycle; external also requires exec/files and local requires port URLs. FC deployment
requires access/toolchain references and exactly one inline/project source.
Inline external mode requires gateway, worker and dispatcher with pinned fc3
components. Native FC props/actions remain adapter inputs, not cloud validation.

`scripts/template_application.py` supplements schema validation with cross-field
budget, binding, hook identity and filesystem containment checks without execution.
Both manifest versions retain existing README, design and catalog checks. Examples
are configuration fixtures, not installable or cloud-accepted catalog entries.

## Alternatives considered

- A second `agent-app.yaml`: rejected because the user requested one configuration.
- Hooks in ordinary sandbox create: rejected because app deployment has different
  ownership, failure, authentication and cost semantics.
- Extending v2 silently: rejected because old consumers may ignore deployment fields.
- Generating IAM/functions from inferred defaults: rejected; inline source explicitly
  describes reviewed resources and component inputs.

## Dependencies

The checker pins PyYAML and jsonschema in `scripts/requirements-spec.txt`; CI installs
these versions. The independent CLI owns app commands, deployment adapter, toolchain
lock, exact artifact/operation receipts and hook protocol:
https://github.com/Alibaba-Agent-Sandbox/agent-sandbox . The independent Python SDK
owns runtime behavior: https://github.com/Alibaba-Agent-Sandbox/python-sdk .
No dependency requires a sibling checkout.

## Test Strategy

Run the existing spec suite plus v3 cases through the same command; preserve all
v2 templates. Cover ordinary v3, direct B, external A, managed B declarations,
inline/project exclusivity, pinned components, unknown fields, invalid types,
paths/symlink escape, missing sources, bindings/budgets, hook IDs/phases/argv,
malformed YAML and all-mode failure classification. Assert checker does not
execute subprocesses. Validate both document fixtures, strict catalog and links.

## Acceptance criteria

- [x] v2 template/catalog checks remain passing.
- [x] Optional v3 application has a canonical closed schema and semantic validation.
- [x] Invalid configurations cannot silently become legacy in all-mode checks.
- [x] Inline configuration avoids a second hand-maintained deployment YAML.
- [x] English/Chinese docs and actual local verification are indexed.
- [ ] Independent CLI integration and current-head remote CI/review/PR merge.
- [ ] FC/model acceptance if an actual deployment claim is made (none in this change).
