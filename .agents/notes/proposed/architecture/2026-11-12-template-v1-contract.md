# Decision: Establish an inactive canonical template v1 admission contract

Status: proposed

## Problem

The unreleased public format needs one local resource entry, optional publication metadata,
Provider-owned stage inputs, and native FC properties. Existing spec5/6 consumers and locked
copies cannot be migrated by renaming the version key. The preceding independent/cross reviews
found unresolved stage paths, configuration references, Managed selection and property ownership.
Tracker: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/309.

## Decision

Add `spec/template-v1.schema.json`, `spec/registry-v1.schema.json` and pure dual-language
normalization under `contracts/template-v1/`. Keep them explicitly inactive until the owner
consumers migrate together. Existing manifests, acceptance scripts, catalog and historical
receipts remain untouched in this scoped change.

The canonical structure separates template preparation from instance creation and embeds a
native Devs project for Serving. Native expressions are preserved, then resolved by the actual
Devs parser before resolved-input and native-component validation. Local resource admission
never reads Registry metadata. Managed roles explicitly reference resources; fixed bridge and
lifecycle facts are generated from the existing profile. Tunable FC props survive, protected
identity/bootstrap props reject conflicts, and compiled secrets remain temporary private data.

Provider selection can remain unbound for offline source intent. Resolved selection must be
concrete and consistent with invocation context. Known adapters use a conservative source-pinned
stage subset; third-party plugins require their actual selected stage validators. This is not
an implementation of every native management API or a new orchestration/secret framework.

## API Design

- `schemaForStage(schema, stage)` / `schema_for_stage`: derive post-native-parser checks.
- `normalizeTemplateV1(raw, validate, options)` / `normalize_template_v1`: synchronous actual
  schema validation, defaults and semantic checks; no expression/config/network execution.
- `compileTemplateV1(raw, validateResolved, options)` / `compile_template_v1`: private execution
  representation, no old public spec marker. Contains sensitive values after native resolution;
  not safe for direct plan/receipt persistence.
- `normalizeRegistryV1` / `normalize_registry_v1`: optional fixed publication metadata and
  existing JSON Pointer question targets; no runtime parameter indirection or secret materialization.

See the bilingual contract README and `.d.mts` for exact fields/options. Validation callbacks
must be synchronous; asynchronous or rejecting Provider validation cannot silently admit a plan.

## Alternatives considered

- Rename only the version or accept both old formats indefinitely: leaves consumers disagreeing
  and retains redundant public contracts for an unreleased product.
- Rebuild all Provider APIs or copy full native FC schemas: invents unsupported fields and
  duplicate ownership; adapter/real component validators remain authoritative.
- Implement near-Devs interpolation or add an engine selector: unnecessary syntax and ambiguous
  semantics; actual Devs parsing belongs to the CLI integration.
- Migrate all active manifests before consumers exist: creates a broken public catalog window.

## Dependencies

The existing Managed profile supplies fixed behavior; canonical defaults are included in the
new contract so independently cloned consumers can load the same bytes. The fixture-only Node
package locks AJV8.18.0; Python tests use existing pinned jsonschema4.26.0. Normalization functions
otherwise use language standard libraries. Provider source revisions are recorded, not treated
as a claim of live cloud acceptance.

## Test Strategy

Consume shared positive/negative fixtures with real AJV/jsonschema validators; compare complete
Python/JavaScript normalized and compiled results. Verify native props, source alternatives,
explicit auth, Provider selection/refusal, pointer targeting, generated conflicts and secret
error boundaries. Batch-check candidate migrations without activating them. Run existing spec,
checker and document checks. Actual Devs, CLI/SDK, image/cloud/model and cleanup gates remain
separate required consumer delivery work.

## Acceptance criteria

- New format has one deterministic staged meaning and optional Registry metadata.
- No old public version, runtime parameters object, callback/internal request body or silent
  unsupported Provider field is accepted by the new envelope.
- Normalization does not mutate input or evaluate expressions; matched language results agree.
- Existing active manifests/checkers remain valid during inactive contract preparation.
- Consumers, actual field forwarding, end-to-end cloud/model behavior and safe cleanup are
  validated before this proposal is called a complete migration or its format becomes active.

## Evidence

- [Verification](../../../evidence/verify/2026-11-12-template-v1-contract.md).
- [Dedicated contract CI coverage](../../../evidence/verify/2026-11-12-template-v1-ci.md).
