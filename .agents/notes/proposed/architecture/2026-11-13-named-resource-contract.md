# Decision: Named static resources with native Serving components

Status: proposed

## Problem

The prior v1 candidate still mixed dynamic-instance configuration, business profiles and
publication defaults into resource deployment. The user explicitly confirmed a smaller final
contract on 2026-11-13 and requested implementation and owner records. This supersedes the
unmerged candidate's public shape, not any historical acceptance result. Track work through
https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/309 and
https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/311.

## Decision

Keep specVersion 1 and name, optional arbitrary author-owned vars, named sandbox resources
and named serving resources. Resource logical names are globally unique. Sandbox template
properties stay under template, including region. Sibling static volumes use that region.
Express properties map to Sandbox/2026-08-20. Serving keeps the component's native props,
with pinned serverless-devs/fc3 components loaded by the CLI's component engine.

buildConfig has exactly one Dockerfile/context or steps branch. Context defaults to the
Dockerfile's directory. An image alone is input; with Dockerfile it is the build/push target;
with native steps it is input. Native steps return a prepared template, not a promised OCI
export. Omission never silently selects a local Dockerfile. Remove public osType, redundant
registry classification/instance inputs, copy/envdInject/installStorageClients and business
profile/instance/access/output/parameter layers. Registry overrides remain optional. Native
startCommand/readyCommand retain template-preparation semantics.

Keep deployer actions at resource scope. Configuration and pre-deploy dependencies cannot
refer to their own resource output. Success/failure/complete actions may refer to their own
output, with missing output handled by the executor. Borrowed template/volume references are
not updated or deleted. Volume retain belongs only to owned declarations; mounts remain
runtime business behavior. Registry initialization parameters use JSON Pointer targets and
never become an ongoing runtime dependency. Secrets reference private environment sources.

Do not lose ordinary applications when removing dynamic fields. Dockerfiles own nonsecret
image defaults and listening metadata. Each ordinary template carries a standalone generated
run.py which creates an instance through the public SDK, injects allowlisted runtime values,
starts its original command, waits for readiness and verifies authenticated discovery. It
generates an application token by default and keeps acknowledged identity/token in an exclusive
0600 session file. Startup failure cleans only the owned instance and retains recovery status.
The original workload/engineering declarations are compared by migration regressions. Managed
Agents API uses native Serving props/actions plus template-owned release code, not a restored
public application block.

## Alternatives considered

Keep all API fields as mandatory author inputs: duplicates reliably inferred data and obscures
common use. Reinterpret native steps as an OCI image exporter: unsupported by the reviewed API.
Freeze runtime credentials in template startCommand: credentials would be bound before the
dynamic instance exists. Drop startup/env/services during structural migration: loses the
existing applications. Reintroduce a generic runtime sublanguage: violates the agreed scope.
These alternatives are rejected. A small template-owned SDK launcher keeps business startup
explicit without another manifest engine.

## Dependencies

CLI execution and initialization are owned by
https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/pull/249 and Registry ingestion by
https://github.com/Alibaba-Agent-Sandbox/registry/pull/102. Consumers copy the schema and pure
normalizers with source locks. Published CLI 0.5.10 does not support this resource contract.
Ordinary launchers use published agent-sandbox-client 0.4.0a7 methods; the actual PyPI wheel
was inspected for create/on_created/envs, start_server/env/command/token and cleanup signatures.
Managed runtime release dependencies remain described by the template-owned deployment code.

## Test Strategy

Use actual JSON Schemas, JS/Python deep-equal fixtures, strict YAML boundaries, invalid build
branches, static volume shapes and resource-cycle cases. Check every catalog manifest,
publication descriptor, bilingual reference and standalone runner generation. Compare original
workloads, startup commands, image defaults and engineering assertions. Test session privacy,
environment allowlisting, startup ordering, cleanup failure and no overwrite before cloud I/O.
The prepared-image acceptance harness must use the same business runner rather than resurrect
removed public instance fields. Local/mock checks do not replace image/provider/cloud gates.

## Risks and Limitations

Source validation does not prove Provider support, account/region availability, real component
deployability or image success. Native steps cannot promise push-back of their final artifact.
The contract consumer locks and CLI CI pin must name actual committed revisions before merge.
Historical receipts retain old source identities; this migration does not requalify them.
Full image/provider/model matrices remain distinct gates. No cloud resource was created by
this owner's local contract/runner checks.

## Rollback Plan

Revert the coordinated source/consumer changes together, preserving historical engineering
records. Do not claim old public data is accepted by this new schema. If later acceptance
creates resources, clean their recorded owned IDs independently before discarding session
files or deployment records.
