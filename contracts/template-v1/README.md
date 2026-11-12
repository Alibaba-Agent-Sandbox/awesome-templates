# Template v1 contract

[中文](README.zh-CN.md).

This directory contains the canonical **inactive** v1 resource contract and pure normalization
functions. Active CLI, SDK, checker and Registry consumers still use their existing contracts.
These fixtures are not deployment recipes until those consumers migrate together.

The resource entry is `template.yaml` with `specVersion: 1` and `name`. It needs a `sandbox`,
`deployment`, or both through a supported `application` consumer. Optional `registry.yaml`
contains publication/initialization metadata and is never read by resource normalization.
There is no required runtime `parameters` object.

## Structure and stage ownership

- `sandbox.template` selects exactly one `source`, `image`, or existing `reference`. Source
  has a relative `dockerfile`, root `context: .`, and optional `profiles` for alternate recipes.
  `template.aliases` retains lookup aliases; it does not authorize replacing another cloud object.
- `sandbox.template.props` contains actual preparation inputs. The known adapter subset is
  CPU count and memory; preparation memory is in MB for Express and backend-specific units
  described in the Provider reference for other adapters. These are not native management API bodies.
- `sandbox.instance` contains the selected adapter's create defaults. `timeout` is the
  high-level lifetime in seconds (1–86400); `envs` and `metadata` are string maps. Declared empty
  environment values retain the existing CLI configuration/injection meaning; this pure module
  neither fetches nor generates credentials. A preparation resource value is not silently
  copied to every create call.
- `sandbox.provider` may be absent in unbound source intent. Execution selects it through the
  existing explicit CLI/config context; a conflicting explicit declaration fails. Resolved
  input always has one concrete Provider. Qualified reference ownership remains checked by
  the actual Provider selector; identifiers are never translated across Providers.
- `sandbox.start`, `ready` and `services` describe one complete workload. The service map
  declares protocol, version and port; an optional operations list is not a permission grant.
- `deployment` embeds the native Serverless Devs 3 project. Its resources retain native
  component identifiers and props. This envelope does not copy FC schemas or implement Devs
  variables, output dependencies, actions or flow.
- `application.type: agents-api` explicitly selects the existing Managed consumer. `roles`
  references three distinct declared resources. `server` selects source or a digest-pinned
  image. `state` and `bindings` carry actual local configuration instead of requiring a second
  hand-maintained binding JSON file. The existing budgets and automatic authentication have
  one default source in `contract.json`. Managed lifetime is authored only as
  `sandbox.instance.timeout` (default3600 seconds); the internal Session maximum lifetime is
  derived from it. Public `sessions.maxLifetimeSeconds` is rejected instead of maintaining
  another editable copy. Idle/turn budgets must fit inside that lifetime.

Known adapters have a conservative actual-input subset. Express permits named-volume mounts
and structured lifetime policy. OpenSandbox permits the currently connected GPU count/security
and selected create options; its current adapter does not accept typed volumes or disk quota.
E2B, Cube and Container instance inputs expose only the confirmed high-level timeout/env/metadata
subset here; unconfirmed resource forwarding is not advertised as backend support. Existing
Container volumes inherited from SandboxSet remain distinct from a typed create-volume field.
The schema does not expose callbacks, internal native request classes or arbitrary management APIs.

Third-party Provider IDs are allowed. Their resolved preparation/create inputs require a
`validateProvider` callback bound to the actual selected descriptor. No callback means refusal,
not permissive passthrough. The recorded revisions in `contract.json` identify this static known
subset; consumers must lock schema selection to the actual implementation and verify descriptor
compatibility. This module does not install or execute a Provider.

## Two validation stages

1. Compile `spec/template-v1.schema.json` with a real JSON Schema 2020-12 validator and call
   `normalizeTemplateV1(raw, validateIntent, {stage: 'intent', provider})`. The result is a copy
   of v1 intent with defaults and consistent role references. Native expressions remain strings.
2. Pass the embedded Devs project and private resource payload to the **official Devs parser**.
   Do not perform regex replacement, implement another expression language, or save the
   resulting secret values in public plans or build artifacts.
3. Use `schemaForStage(schema, 'resolved')` with the real validator, then
   `compileTemplateV1(parsed, validateResolved, {provider, validateProvider})`. This rejects
   missing type/value results and creates private fields for existing execution services.
4. Validate actual native props with the selected component's own schema and check the selected
   Provider descriptor before any resource changes. Contract validation is not component or
   cloud acceptance.

Both JavaScript functions accept a synchronous validation function returning a boolean or
throwing on failure. Python equivalents use snake_case and accept `jsonschema`'s `.validate`.
The normalizers do not read process environment, current-directory files, credential stores,
Registry metadata or cloud APIs. `compile` emits no old public spec5/6 marker.

Private compiled fields include `name`, `kind`, optional `sandbox`, native `deployment`,
preparation `resources`, `env`, `provides`, `ports`, `start_cmd`, `ready_cmd`, native reference
or image, lookup aliases and alternate `build_profiles`. Managed input additionally compiles
existing `application` fields, `roleResources`, native `roleProps`, and `bindingValues`.
**Binding values, native environment props and compiled application inputs may contain secrets;
these results are temporary execution data, not a safe receipt/plan serialization.**

Managed generated function identity/description, private environment keys and bridge
image/port/entrypoint/command cannot be authored in native props. Other props such as
`memorySize: 4096`, CPU, logs and VPC survive unchanged for the actual consumer. The bridge
runtime is custom-container. The current coordinator uses one component version, one resolved
region and one function RAM role; declared role inputs cannot conflict with its internal role
binding. New multi-role IAM or generic Managed lifecycle semantics are not inferred.

## Optional initialization metadata

`spec/registry-v1.schema.json` defines package identity/version, bilingual descriptions,
author/license, tags, READMEs, the resource entry, and optional questions. Questions use
standard non-root JSON Pointers into the normalized resource document. Targets must exist;
duplicate/stale/invalid paths fail. The target value and target schema own defaults and types;
questions cannot define a second runtime default or arbitrary field structure.

Sensitive questions name an `environmentVariable` and target that exact native
`${env('NAME')}` (or double-quoted equivalent) expression. This is a consistency check, not
expression evaluation. Collected secret values belong to private configuration/environment,
never to the target YAML literal. `normalizeRegistryV1` validates this linkage; it does not
collect, save or apply question answers. Consumer initialization must validate materialized
nonsecret values against the selected target schema before writing them.

## Local contract checks

From this repository, install the existing pinned Python checker requirements and use
`npm ci --prefix contracts/template-v1`. Run the Python contract suite and the Node suite
(`npm test --prefix contracts/template-v1`); set `PYTHON` if the desired Python environment is
not the default. The Node suite invokes the Python consumer and compares complete normalized
and compiled results. Fixtures include all five known Provider subsets, an actual alternate
Python recipe, unbound and bound source, native expressions, FC/domain intent, Managed roles,
private bindings, no Registry, and invalid stages/fields/references/conflicts.

The existing repository specification/checker/document checks remain mandatory. Real expression
execution belongs to the CLI parser integration; build/deploy/model/cleanup acceptance belongs
to the corresponding implementation delivery. Tracker:
[awesome-templates Issue309](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/309).

`sandbox.ports` optionally declares additional access ports (unique integers1..65535). Compilation returns the sorted union with real services.port values. Raw ports promise no running service, protocol or public Gateway route.
