# Decision: original AppWorld engine with private runtime unpacking

Status: proposed. Refs https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/70.

## Problem

Issue70 requests original AppWorld0.1.3.post1 execution, a real task/model score and Express acceptance; the original survey had not established whether Docker was required. Immutable upstream66ad8099e12188ece0d3fe45e661dbc01880813b documents direct Python execution and optional Docker.

## Decision

Implement the original published appworld0.1.3.post1 engine/evaluator in an isolated Linux Python3.13 runtime. Use an explicitly described authored compatible-model bridge around original AppWorld.execute, not a claim that the historical paper baseline was reproduced. Preserve original environment safety defaults. No model-generated code executes on the operator.

Keep protected upstream app/data bundles encrypted in distributable images. Unpack only into a per-call private disposable cloud runtime; never export decrypted protected code/data or raw task contents as public evidence. Actual current runtime/model/provider acceptance is recorded in the dated final evidence; scope remains one original training task.

## API Design

Scalar appworld_version/appworld_setup_check/appworld_native_smoke, appworld_run(task,max_steps,command_timeout) returning original native score and owned encrypted artifacts, and appworld_verify_artifact(path,task) independently re-evaluating saved native databases without model settings. Complete bounds/results are documented in both README languages. Credentials require an explicit approved base URL; no default vendor fallback.

## Alternatives considered

A Docker-only design is unnecessary according to the pinned upstream. A similarly named API mock does not establish AppWorld execution. Shipping an already-unpacked public image conflicts with the protected-portion license. A model marker or static score does not qualify a task.

## Dependencies

Original published wheel0.1.3.post1:625317bytes/SHA256db77f8003982502383a50fa2974983894bd1c54f64e2fd3f7e1540d5edd037eb. Original official data-0.1.0.bundle:34280074bytes/controller-measured SHA256fd9f9608c2ec71ed0ac25c3633a738b9129a318a129e31230425b9188e508250, not an upstream-published checksum. Public source Apache2.0; protected app/task/data portions impose encrypted public redistribution. Full Python hashes and native package compatibility must be checked before cloud mutation.

## Test Strategy

Authored scalar/ownership/credential/output guards, source-only HTTP with native/model omissions explicit, actual image pin checks, source-bound canonical steps and SDK-created Express deployment. Real model completes one original training task; original native evaluator and separately reloaded result/database state reproduce the score. Preserve every failure/skip. Independently verify owned native/private/process/listener/sandbox/template/cache cleanup.

## Acceptance criteria

- Original engine/source/package/data identity, license boundary, isolated pinned runtime and all bilingual/template/design/catalog contracts agree.
- No decrypted protected content is publicly redistributed; no model-generated code runs on the operator.
- Actual original task/model/evaluator and independent artifact/score checks pass on SDK-created Express.
- Current image/steps/local/spec/docs/CI checks pass and owned cleanup is independently confirmed before qualification and merge.
