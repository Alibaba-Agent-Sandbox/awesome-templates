# Audit: named-resource migration still needs a real dynamic startup contract

- Date: 2026-11-25
- Result: BLOCKED (full migration activation); read-only/source review complete
- Draft examined: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/311 at ee59a726bb04e9b67a79b1bcbbb0a528ced11ef1
- Related consumer: https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/pull/249
- Current bounded API-publication fix: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/317

## Finding

The draft's ordinary template.yaml files contain static named Sandbox template resources and no dynamic instance startup. For example, python-hello's Dockerfile installs its service and declares ENV/EXPOSE but no executable application startup. Its generated run.py is therefore functional, not redundant: it creates an instance, forwards allowlisted runtime environment, starts the application with the public SDK, waits for readiness, and checks authenticated discovery.

The draft then asks users to run this extra Python launcher, manage .sandbox-session.json, extract its application token and call the retired `abx sandbox command` tree. Those instructions conflict with the approved simpler create/use workflow and private internal-state handling. Deleting run.py or replacing that command with bare create would lose service startup; it is not a valid cleanup.

## Provider and server facts

The official custom-template guide describes startup/readiness during template build and a running-process snapshot. It explicitly explains that creating instances does not rerun startup, and OCI ENTRYPOINT/CMD are not the execution mechanism for this Express flow. Its examples distinguish systemd service environment from later execution environment. Source: https://help.aliyun.com/zh/agent-sandbox/build-and-manage-custom-templates-with-code (reviewed 2026-11-25; page updated 2026-11-23).

The environment-variable guide demonstrates create-time envs being available to later command execution; it does not establish that a snapshotted HTTP server reloads them. Source: https://help.aliyun.com/en/agent-sandbox/environment-variable . The native API metadata has envVars for instance creation, without an equivalent instance startup/entrypoint field: https://api.aliyun.com/meta/v1/products/Sandbox/versions/2026-08-20/api-docs.json . Some Create/Update descriptions disagree on generation wording; that discrepancy is not a reason to infer unverified behavior.

The current Python Server SDK reads ABX_SERVER_TOKEN into auth_token at application construction, then constructs PolicyEngine using that value. The policy runtime initializes token state at construction. The inspected source does not provide a create-time environment hydration path for that existing process. Fixed source: https://github.com/Alibaba-Agent-Sandbox/python-sdk/tree/76c7e68bd9cc73f52c4ddf9545656ed4bcd1f847/server-sdk/src/agent_sandbox/server .

Earlier owned evidence is consistent with this boundary: [prewarmed-server configuration](2026-10-16-prewarmed-server-configuration.md) observed that create-time environment did not configure the existing server, while a fresh process through the native execution API worked. [Prepared startup environment](2026-10-25-native-prepared-startup-environment.md) concerns launcher/process environment; it does not prove snapshot hydration.

## Cross-review and decision

The contract reviewer read the draft's template, Dockerfile, generated runner and README. The CLI/API reviewer independently checked official provider semantics and current Server SDK authentication construction. Root review rejected stripping the startup stage or introducing an unapproved lifecycle metadata/signing/hydration language merely to complete the migration.

A functional final migration needs an explicitly supported create-time startup/bootstrap route with runtime credentials, readiness, failure cleanup and ownership, or a real supported snapshot reconfiguration contract. Neither can be inferred from OpenAPI help metadata, OCI listening ports or template-preparation startCommand. The existing API-publication fix remains valid independently.

The attempted merge of current main/API-publication changes into a new isolated draft-review branch found conflicts in README/spec/usage guides and two engine-template manifests. It was aborted without editing or publishing draft migration content; existing work and historical records were preserved. Current main's exact database/document image-source fixes must survive any later coordinated migration.

## Remaining acceptance

- Define and implement the supported dynamic startup route without exposing internal session files or sharing a frozen token across unrelated instances.
- Verify at least one real ordinary template on Express and OpenSandbox, including create-time token, API invocation, failed startup cleanup and independent deletion; do not extrapolate one backend's process semantics to the other.
- Then migrate all template startup/environment/API declarations and their bilingual examples, preserving existing image/source fixes and source ownership.
- Reconcile CLI249, templates311 and Registry102 consumer contracts before activation; a schema pass alone is insufficient.

No cloud resource, credential, model request, package release or new runtime mechanism was created by this audit. This is a concrete unresolved semantic prerequisite, not a claim that the full requested migration is complete.
