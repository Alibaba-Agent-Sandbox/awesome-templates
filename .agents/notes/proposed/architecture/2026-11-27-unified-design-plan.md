# Decision: Deliver template contracts and examples for the unified user flow
Status: proposed

## Problem

The target design gives template authors one deployment-resource file, code-defined services and optional client helpers. Existing template specifications, skeletons, checks and examples describe older YAML and invocation paths. A schema-only migration would leave deployment, application-description delivery, SDK-only usage and CLI/MCP helper consumption disconnected.

This repository owns template source, the template and Registry authoring specifications, checkers and catalog entries. Python owns neutral runtime contracts and the Python Client/Server implementations; Node owns the target Node Client/runtime/source-preparation and Server SDK implementations. The CLI owns deployment execution. This record plans template work against those interfaces and does not claim the proposed YAML or SDK methods are already executable.

## Decision

Deliver the following tasks in dependency order. Keep one current authoring specification and preserve historical evidence; do not copy the full unified product design into each template.

| Task | Delivery interface | Order and completion boundary |
| --- | --- | --- |
| TM-01 | `specVersion: 1` template/Registry schemas, semantic checks and authoring reference | After neutral contracts are agreed; align resource fields and source branches before changing examples |
| TM-02 | A code-first service example with the Server SDK's generated application description and an ordinary SDK-importable module | After the Server export contract and CLI extraction interface; prove description-to-artifact association and both creation paths |
| TM-03 | A source-distributed helper example with Python/Node packages, static operation metadata and Registry recommendations | After Client helper/source-preparation interfaces; prove independent CLI and SDK preparation without public package publication |
| TM-04 | Complete service, combined-tool and Serving examples with documented inputs, real protocol calls and owned-resource cleanup | After their Providers, Client/Server methods and deployment adapters are available; qualify each example separately |
| TM-05 | Bilingual README/authoring guidance, optional task Skills, skeleton and catalog updates | With each delivered example; publish qualification only for fixed artifacts and observed behavior |

Start with the representative code-first and helper flows, then extend the remaining examples. Do not mass-rewrite the catalog or add unrelated CLI/SDK releases solely to make a plan look complete. When a necessary runtime interface is missing, record and link its owner task; do not replace it with template-specific runtime machinery.

## API Design

TM-01 preserves `template.yaml` as the deployment-resource configuration. It defines `sandbox.<name>.provider/template` with optional role, volumes and actions, and `serving.<name>.component/props/actions` using supported component-native fields. Names in the file are logical resource keys, not cloud IDs. `registry.yaml` supplies package identity, initialization parameters and client recommendations; it is not a second runtime configuration. Keep `parameters` out of `template.yaml`, and do not introduce `instance`, root `apis`, bindings files or a batch undeploy replacement.

| Author interface | Delivery and validation |
| --- | --- |
| Template sources | Distinguish borrowed template, existing image, Dockerfile and native Steps branches; preserve template region and native preparation semantics; do not claim Steps export an OCI image without evidence |
| Variables and dependencies | Validate the documented expression subset, types and phases; unresolved upstream outputs stay pending until real deployment results exist; secrets reach only their actual consumers |
| Creation defaults | Publish only the agreed non-secret `createInput` fields: actual source, optional role and named volume mounts; no credentials, arbitrary metadata, application binding or internal receipt paths |
| Registry parameters | Resolve existing JSON Pointers to allowed scalar values or matching private-input references; initialize the actual consumer without adding another parameter type/default table |
| Registry styles | Declare `resource/style/service/default` and `clients.node.source` or `clients.python.source`; accept template source directories, fixed Git sources and optional exact package coordinates |
| Application description | Consume the Server SDK's versioned export with its artifact association, services, protocol/port/authentication/contract and optional startup/readiness instructions; deliver the same generated object to CLI extraction and an ordinary author module for explicit SDK import |
| Optional helper | Supply normal language package metadata and dependencies, an explicit factory and, when CLI/MCP are supported, static operations bound to the same typed methods |

TM-02 must show how the author produces and imports the application description; an unexplained `application_source` argument is insufficient. It is generated author metadata, not a user-maintained binding file or an SDK dependency on CLI private state. Existing image/reference sources with no applicable description promise native instance creation only. Calling an existing known service does not require an application description or authorization to start it. Platform startup and instance runner startup must not both run for the same service.

TM-03 exposes one demonstrable flow: caller-local file path → bounded upload → business request → returned report. Node CLI/SDK/MCP share the Node implementation; Python SDK/MCP use the Python implementation of the same business contract. Source installation is explicit and produces portable ordinary project dependencies. Initialization, help, import and business calls do not install packages. A template author may provide one language only; missing languages or static operation catalogs are reported, not inferred or replaced through another language.

The helper's HTTP methods must consume the Client's actual response/error contract, including status, body and cancellation. A temporary test transport cannot establish compatibility with the production Client. Static metadata generates CLI/MCP projections; the template does not create a second HTTP stack, installer or MCP protocol implementation. Optional task Skills explain the real preparation, target, result and cleanup steps without treating installation of a Skill as installation of its code dependencies.

Authentication remains service-specific. The five Express service examples explicitly use platform-entry mode: confirmed public traffic permits anonymous application access, protected traffic uses the Provider-retained traffic credential, and unknown policy or missing credentials fails without fallback. Their Server policies expose only intended business methods. Other services that explicitly select the MD5 application rule use the actual template and instance IDs on both sides; they do not describe the derived value as strong authentication or a native platform token. External Serving retains its own actual ingress authentication.

The HTTP-without-envd example stays an unqualified candidate until a real supported preparation path proves that envd was not injected and that the service, authentication and cleanup work on the target platform. A Python base image, local container response or schema pass does not establish that result. Do not make the checker claim it can detect an undeclared no-envd intent.

TM-04 covers the existing-service HTTP, named-command, OpenAPI and combined-tool paths without silently changing protocols after failure. Serving examples use real component configuration and explicit application URLs; dynamic Session instances and application data have their own cleanup. `template build` prepares artifacts, `deploy` publishes resources, create is explicit, and local close does not delete a borrowed instance. Cleanup uses actual instance/template/volume IDs or the platform's management interface.

### Follow-up contract clarification

TM-01 owns initialization authoring semantics; TM-03 owns helper failure/cleanup examples; TM-04 owns authentication examples; TM-05 owns aligned guidance. These refinements stay within the existing tasks; no additional subsystem or completed implementation is implied.

Initialization prepares and validates the complete source in its own staging directory, saves explicitly collected private inputs and preferences for the final path, then publishes into an absent or still-empty destination without overwriting concurrent files. Failure before publication leaves no partial target source; report already-saved private inputs and allow rerunning the original init command. Ordinary unsaved answers are collected again and a changed source version is shown. No cross-store transaction, nonempty-directory takeover or resume command is introduced. After publication the directory is valid; an output failure must not delete it or suggest overwriting it with init.
The CSV Serving example is an explicitly selected custom-Bearer flow, not a default automatic-token flow. A declared sensitive input collects or reuses an existing application-managed value; absent values fail before deployment, and repeat deployment does not generate or rotate it. CLI private configuration does not populate SDK process environments. SDK-only callers explicitly supply the same existing value from their application's own configuration; no CLI dependency, implicit secret retrieval or second random token is allowed. Normal no-manual-token examples use their declared platform or FC-signed ingress. Do not change only the FC trigger and claim the old Bearer service supports signing.
A received upload identity remains observable when a later helper stage fails. Preserve the original exception/HTTP details and recognizable cancellation, with safe progress containing the completed stage, known file ID and actual cleanup state. An unknown submission is not safe to replay or automatically delete. Explicit file deletion affects only the caller's selected upload, never a borrowed instance. MCP cancellation/disconnection cannot guarantee delivery of a final error or identity; do not add a recovery daemon or claim durable recovery from exception fields.

Raw HTTP request/invoke keeps its status, allowed headers and body, including non-2xx. CLI and MCP adapters use actual HTTP executor metadata to report non-2xx as failure, not the presence or absence of an exception or an arbitrary business `error` field. A submission returning 202 is accepted, not completed; a completion-promising helper must observe its actual terminal contract. Successful tool output schemas do not constrain error content. Keep native E2B/OpenSandbox exception and process-result semantics intact.

Default MD5 application authentication requires both sides to know the same real instance and historical cloud-template identity. Native connect may obtain platform traffic credentials without recovering that association. A Provider-verified mapping or an explicit caller assertion based on original creation facts may supply it; current Registry aliases, downloaded source and unverified runtime fields may not. The optional shared service binding `template_id` fills an unknown association only, never overwrites a confirmed identity or changes server-side identity, and is distinct from a platform-verified mapping. Compare only identifiers with the same confirmed semantics. Missing identity disables that authentication branch, with no alias guessing or authentication downgrade. The derived value is not strong authentication.

The report service supplies bounded explicit deletion by received file ID. Its helper checks the real HTTP completion status rather than assuming every 2xx JSON body is a finished report. Document the bounded in-memory lifetime and the absence of durable recovery after disconnect; never suggest deleting an entire borrowed instance to clean one upload. Existing schema fields are sufficient for the custom-Bearer sensitive input.

## Alternatives considered

- Moving parameters or helper installation metadata into `template.yaml` would duplicate initialization and runtime inputs. Registry metadata and ordinary code dependencies already cover those tasks.
- Handwriting a second application API manifest would drift from Server registration. Generate the description once and test its actual consumers.
- Requiring npm/PyPI publication would unnecessarily exclude template-local and fixed Git helpers. Ordinary source packages are valid preparation inputs.
- Making every example import a CLI engine, read CLI state or export an application token would break SDK-only production usage.
- Treating all services as Server SDK services would invent named routes and discovery behavior for ordinary HTTP or envd/execd protocols.
- Removing envd from a Dockerfile and immediately marking the example qualified would confuse image contents with platform preparation behavior. The explicit qualification gate is narrower and observable.

## Dependencies

The companion records below target `main`. Each link becomes available when that owner's planning PR merges; publishing a plan does not establish product delivery.

- [Python contracts and Client/Server plan](https://github.com/Alibaba-Agent-Sandbox/python-sdk/blob/main/.agents/notes/proposed/architecture/2026-11-27-unified-design-plan.md): neutral contracts/fixtures, Python service export, application preparation, helper response and lifecycle behavior.
- [Node Client/runtime/source-preparation and Server plan](https://github.com/Alibaba-Agent-Sandbox/nodejs-sdk/blob/main/.agents/notes/proposed/architecture/2026-11-27-unified-design-plan.md): matching Node author/consumer interfaces, independent preparation and Node helper/MCP consumption.
- [Provider plan](https://github.com/Alibaba-Agent-Sandbox/awesome-providers/blob/main/.agents/notes/proposed/architecture/2026-11-27-unified-design-plan.md): catalog plugin contracts, supported source/create mappings, real identity and access-state handling; built-in Express implementation work remains with its Client owners unless separately reassigned.
- [CLI plan](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/blob/main/.agents/notes/proposed/architecture/2026-11-27-unified-design-plan.md): YAML execution, component adapters, build-description extraction, initialization, private inputs and CLI/helper projection.
- [Registry plan](https://github.com/Alibaba-Agent-Sandbox/registry/blob/main/.agents/notes/proposed/architecture/2026-11-27-unified-design-plan.md): static ingestion of both authoring files, source recommendations and accurate CLI/Python/Node/MCP support display.

TM-01 can proceed with fixed contract fixtures. Runtime export and consumer support must land before executable examples depend on them; Registry consumes the resulting authoring schema rather than defining another version. Normal package dependencies must be available before user-facing release instructions name them. The proposed record for this repository uses the same candidate branch and path.

## Test Strategy

For this documentation-only plan, run applicable record/link checks and identify same-batch references as pending. Do not run cloud tests merely to validate the ADR, and do not infer product execution from document checks.

For specification/checker changes, use the repository's required `python3 scripts/test_spec_tools.py` and `python3 scripts/check_template.py --all`, extended with the new positive and negative fixtures. For an individual template, run its checker and regressions, then the applicable local/image/cloud/model tiers. Existing L0–L4 evidence remains historical; adapting command paths must not silently relabel past results as acceptance of the new contract.

Test source branches, expression phases, removed/unknown fields, logical versus real identities, volume/role creation defaults, Registry parameter pointers and language-specific helper sources. Confirm that removing `registry.yaml` after initialization does not change build/deploy values. Verify fixed dependency artifacts and generated descriptions before image and cloud runs.

The application-description test uses the actual Server export and both CLI and SDK consumers. The SDK test runs without abx or CLI configuration and imports the generated author module. The helper test installs source packages into independent Node and Python projects, then invokes the same packaged methods through SDK and the supported CLI/MCP projections. Exercise success, HTTP failure, upload failure, cancellation between steps, missing dependency and close behavior; retain the local-only limits of test substitutes.

Cloud verification checks actual public/protected/unknown access handling, real service readiness, one creation/startup, business responses and independent owned-resource cleanup. The no-envd case additionally verifies the actual prepared/runtime service inventory through a reliable platform path before claiming absence. Agents/Serving examples require their real business result and Session/data cleanup; a model-free smoke test is not real-model acceptance. Reuse one controlled environment where possible and do not create unrelated databases or deployment revisions to fill a matrix.

Publication or document checks do not move this implementation plan to `implemented`; that requires the applicable product acceptance criteria and the repository lifecycle rules.

## Acceptance criteria

Follow-up acceptance also requires:

- Validate the complete custom-Bearer Registry parameter and matching environment reference, both languages of guidance, missing-input behavior and explicitly provided SDK identity.
- Exercise real local HTTP success, upload-then-422, cancellation before report, and deletion that preserves another upload and releases capacity; distinguish a test transport from the production SDK.
- Check source publication failure paths and authentication identity prerequisites in executable consumer acceptance; schema validity alone is not proof.


- TM-01 has one consistent v1 authoring contract and semantic checker across complete examples; no additional user binding or internal state file is required.
- Initialization writes actual supported inputs, preserves private references and temporary override semantics, and does not install or execute helper code.
- TM-02 delivers a real generated description and ordinary SDK import path. CLI and SDK consume the same applicable service contract without duplicate startup or CLI-state dependence.
- TM-03 works from unpublished template source or fixed Git in independent CLI, Python and Node consumers; declared CLI/MCP projections use the same helper methods and preserve HTTP failure/cancellation behavior.
- Platform-entry and explicitly selected MD5 application modes are distinct in code, documentation and verification; no missing-credential fallback makes a service anonymous.
- The no-envd example remains unqualified until real platform evidence establishes the claimed absence and complete business/cleanup flow. An unsupported path is documented honestly.
- Each claimed template/provider tier has fixed-source, observable evidence and independent cleanup results. Schema validity, local HTTP success, image build and cloud/model acceptance remain separate.
- Bilingual READMEs explain configuration, actual CLI/HTTP/SDK paths, customization and user-owned cleanup. Internal acceptance details stay in engineering evidence, and catalog qualification does not precede the required real checks.
- The ADR remains proposed until its record and contribution gates pass; future implementation tasks and releases are not marked complete by publishing this plan.

Document validation and review disposition: [verification](../../../evidence/verify/2026-11-27-unified-design-plan.md).

Follow-up review and verification: [failure and authentication contracts](../../../evidence/verify/2026-11-27-feedback-contracts.md).
