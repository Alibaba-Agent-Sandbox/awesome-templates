# Shared application profile defaults

## Problem

Managed manifests repeat fixed runtime, protocol and role values. Template checks,
CLI and Registry identify the same application using different literals or the
schema version. This increases authoring cost and permits consumer drift.

Tracked by https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/302;
CLI coordination: https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues/244.

## Decision

Own a small JSON default table with pure Python and JavaScript expansion in this
repository. Select an application using its explicit deployment profile. Keep
spec versions 5 and 6 as supported validation contracts. Expand only absent keys
before strict validation; explicit nulls and conflicts must remain invalid.
Simplify agents-api only, increment its template version to 0.1.5 and retain all
historical execution evidence. Do not migrate ordinary templates or qualification.

## API Design

`applicationProfile` / `application_profile` read the declared deployment profile.
`normalizeApplicationProfile(manifest, catalog)` and its Python equivalent return
a deep copy. Defaults include fixed API/runtime/lifecycle/output fields and role
routing for existing bindings. State and ingress roles follow their named refs.
The caller must perform complete schema/semantic validation after expansion.
Additional bindings still require explicit targets. Secrets, provider, budgets,
region, images and resource sizes are not synthesized.

## Alternatives considered

A new spec version or general deployment language would increase scope without
improving the current closed profile. Duplicated consumer defaults would preserve
the inconsistency. Keeping every fixed field mandatory adds no author choice.
Defaulting conflicting values would hide mistakes and permission changes, so it
is explicitly rejected.

## Dependencies

Land this shared contract before consumers. CLI must expand before its schema and
semantic validation; Registry consumes the same source bytes and classifies by
profile. CLI 0.5.10 does not support compact manifests. No runtime dependency,
Dockerfile, model provider or cloud topology changes are made here.
Registry consumer: https://github.com/Alibaba-Agent-Sandbox/registry/issues/94.

## Test Strategy

Use identical Python/JavaScript fixtures for expanded, compact, custom-reference,
legacy and invalid-profile inputs. Assert idempotence, nonmutation and exact
expanded runtime equivalence of the actual agents-api manifest. Regress explicit
null/conflicting fields, missing credentials, unauthorized role/env routing and
version/profile independence. Run required spec, catalog and documentation checks.

## Acceptance criteria

- Compact and expanded inputs produce the same validated runtime contract.
- Invalid profiles, explicit conflicts and credential-role crossings fail.
- Both language implementations pass the same fixtures.
- Existing v5 manifests and evidence remain byte-for-byte unchanged.
- Consumer changes and bilingual usage documentation land before advertising
  the compact manifest as supported by a published CLI.
- Local evidence records actual passes and delivery limitations separately.
