# Template workflows and verification

A template provides software and services. A provider supplies sandbox operations and endpoint resolution. A CLI or SDK supplies a particular protocol client. A workflow names the complete path through these layers. [中文](workflows.zh-CN.md).

## Current machine contract

Every source and application manifest uses `spec_version: 4` and `workflow_contract_version: 1`; the catalog uses `schema_version: 2`. Earlier schemas and the retired `capabilities`, `tested_on` and `providers` machine fields are rejected. There is no compatibility mode.

The normative schema is [template-v4.schema.json](../spec/template-v4.schema.json). [Shared operation contracts](../spec/contracts/workflow-v1.json), [verification profiles](../spec/contracts/verification-profiles.json) and [receipt schema](../spec/contracts/receipt.schema.json) are offline copies of the [Python contract owner](https://github.com/Alibaba-Agent-Sandbox/python-sdk/tree/main/contracts). Their lock records source revision and content digests. Synchronize them through `scripts/sync_workflow_contracts.py`; do not edit copies manually.

| Field | Meaning |
| --- | --- |
| `provides` | Named services with exact protocol/version, port and operations; ordinary Python does not imply an interpreter protocol |
| `workflows` | Named complete paths with input kind, startup policy, binding, selected operation and additive requirements |
| `default_workflow` | Exactly one existing workflow ID, explicit even for a single path |
| `binding` | Transport, endpoint source, caller location and authentication audience; host and guest are different paths |
| `required_operations` | Additional known shared operations; cannot remove derived create/delete, prepare, startup or endpoint requirements |

An application workflow selects a declared service and one operation it provides. An exec workflow selects `exec.run` or `exec.stream`. An interpreter workflow selects an exact code operation, such as stateless `code.execute`, persistent `code.default-context.execute` or `code.context.execute`. Context creation/deletion and real-time streams are separate operations. A buffered callback is not live streaming.

Source inputs require preparation. An image is not an E2B/Cube/container native template ID. Managed inputs bind to their declared provider. The provider's accepted inputs and startup modes are checked before side effects. `startup: exec` requires an explicit startup command and exec; `entrypoint` requires real platform support and must not be silently substituted with exec. External services use their own binding and do not gain cloud lifecycle support.

## Deployment topology

The optional `application` mapping retains external/in-sandbox placement, gateway, deployment adapter, hooks, durable state, bindings and limits. Deployment hooks are host deployment actions. They do not run during template checks, imports, image preparation or sandbox startup. Both documented [local](examples/application-local/template.yaml) and [external](examples/application-external/template.yaml) examples use the current workflow schema without changing this topology.

## Planning and execution

The planner checks the selected workflow and actual consumer: CLI, Python Provider, independent ServerClient or native SDK. Platform-native support does not prove that the project adapter or a language bridge implements it. Application HTTP can work without the unified interpreter; an interpreter failure cannot silently execute a shell script instead.

Static outcomes are satisfied, unsupported or unknown. Configuration, authorization, reachability, runtime readiness and protocol mismatches remain distinct. Local preflight must resolve required unknowns before payload execution. A directory page cannot inspect a visitor's credentials or deployment.

Source preparation preserves Dockerfile FROM, USER, COPY and ENTRYPOINT. Unresolved placeholders fail preflight. The execution snapshot binds source, effective configuration and provider code before use; later edits invalidate the plan. Keep platform API keys, gateway headers and service tokens separate. Endpoint joins preserve proxy prefixes and queries; redirects and unauthenticated retries are refused.

Persist resource intent before push, registration or create, then record returned IDs. Unknown responses need reconciliation, not blind create retries. Only owned resources may be removed. A retained image or template requiring manual deletion is a residual, not complete cleanup.

## Evidence and project certification

Every receipt identifies workflow, binding, consumer/version, contract/profile digest, source/manifest/build/artifact/provider identities, execution time, check IDs and cleanup. A mutable template ID alone is insufficient: updates can change its image/runtime. A source-image guest test cannot certify host HTTP, unified CLI launch or Python Provider invocation.

Normative profiles have stable required checks. Source applications require prepare, create, start, protocol, invoke, endpoint and independent cleanup. Missing, FAIL or required SKIP results cannot pass. Authors may add checks, not remove the profile minimum. Model and external-service scopes remain separate.

Author reports, local reproducible reports and project-recognized CI evidence are different classes. Only independently authenticated, maintainer-approved workflow/runner/revision/artifact provenance can derive project verification. Writing `PASS`, `cleanup_verified: true`, a runner name or a fabricated hash into JSON cannot confer trust. Templates cannot expand the runner allowlist.

Historical receipts remain immutable and retain their original scope. They are not converted to the new schema or reassigned when a default workflow changes. Current README sections therefore do not repeat old provider pass tables as new workflow certification. Managed catalog `historical_evidence` links the original reports without claiming current support.

Provider Beta/Stable maturity remains an independent maintainer decision. A missing unified interpreter operation means that interface is not adapted; it does not mean that a template's Python or application service cannot run.

## Validation

Install `scripts/requirements-spec.txt` with the repository's locked dependency versions. Run `scripts/test_spec_tools.py`, `scripts/check_template.py --all`, `scripts/check_managed_catalog.py`, workflow regressions and `scripts/check_docs.py`. These are local checks; real-backend workflow claims additionally require exact-path execution and independently confirmed cleanup. No current template receives project certification merely from this schema update.

## Explicit build profiles

A source may declare `build_profiles.<id>: {dockerfile: Dockerfile.<id>, context: "."}`.
The caller chooses `--build-profile <id>` explicitly; no profile is inferred from a
provider name. The default Express recipe keeps its platform base and contract.
A separate profile may use another digest-pinned base while retaining non-root
execution and pinned runtime dependencies. Every selected file is part of the
immutable source/build identity. Providers preserve the recipe's FROM, USER, COPY
and ENTRYPOINT bytes. `python-hello` supplies `portable` as the first such profile.
A declared profile or a passing source checker is not an image/native acceptance.
