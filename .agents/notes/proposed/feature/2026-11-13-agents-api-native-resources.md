# Agents API on named resources

- Status: proposed implementation, local verification complete for the recorded scope.
- Owner: awesome-templates, agents-api recipe and its business bootstrap.
- Related: [template PR 311](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/311), [CLI PR 249](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/pull/249).
- Verification: [local evidence](../../../evidence/verify/2026-11-13-agents-api-native-resources.md).

## Decision and scope

The user removed the public application/deployment wrapper and required native FC props,
while retaining actual Agents API authentication, sessions, upgrade and cleanup behavior.
Merely deleting the old block was rejected: the pinned SDK consumes concrete runtime JSON,
and native function deployment does not publish a Gateway alias or initialize database identity.

The recipe now declares one named Sandbox template and three native FC resources. Its
arbitrary vars hold reuse values and business policy; registry.yaml parameters only guide
initialization. The Guest is prepared without a native authenticated-service start/ready command. Worker owns dynamic
Sandbox instances and explicitly starts the bridge only after injecting each instance's private environment. Native FC actions build the Server image; template-owned release.py
coordinates application tokens, immutable Worker/Dispatcher names, state identity, candidate
verification, stable alias and dispatcher timer. The Server entrypoint compiles scalar FC
environment into the actual pinned SDK's configuration contract. Gateway receives only the
business-token digest; Worker alone receives model credentials. Platform keys do not enter
the Guest via this recipe.

Default business/internal tokens are generated and securely reused in private local files.
Explicit process tokens are not copied to the credential store. Internal-token changes are
rejected while retained revisions rely on the same invocation key. Server builds require a
new explicit tag for an update. Historical Workers remain available for existing Sessions;
there is no automatic historical-revision retirement in this recipe.

## Adversarial review and resolved counterexamples

1. The native Devs parser's file() returns text and cannot execute a policy compiler;
   JSON.stringify expressions are not a supported serialization escape. The pre-deploy
   script reads this recipe's literal policy and prepares private scalar environment values.
   The CLI rereads native expressions after hooks without rewriting template.yaml.
2. Candidate tasks can be claimed by the old Dispatcher, which lacks the new Worker route.
   The new Dispatcher therefore takes over old/new routing, with trigger readback, before
   candidate creation and smoke. Candidate failure does not change prod and leaves the new
   Dispatcher serving retained Sessions; this is not described as a rollback.
3. A stale drain flag cannot authorize deletion after a database/function replacement.
   Each control operation verifies the recorded Dispatcher function ID and signed status's
   database identity before draining, and rechecks the returned identity. Every destroy
   performs fresh drain verification; it does not trust a cached flag.
4. SDK FCTaskSender requires a host-only FC endpoint, not an HTTPS URL. An actual installed
   pinned SDK test covers compiled configuration, native provider bootstrap, signed invocation
   compatibility and this endpoint boundary.
5. A native snapshot startup cannot replace dynamic startup after authentication injection.
   The actual pinned SDK ManagedExpressBackend already creates with envVars, records
   ownership, prepares the session and explicitly starts the managed bridge with process env.
   Native start/ready was removed from this recipe; a real SDK fake-infrastructure regression
   verifies creation, ownership persistence and authenticated startup order. Engineering
   startup classification is private test metadata, not a public resource field.
6. Public docs must not retain old app commands or promise automatic recovery. Both languages
   explain native resource configuration, token sources, retained revisions, drain-aware
   removal, and the absence of automatic rollback/resume for uncertain publication.

## Remaining boundaries

This change has not run a new complete FC-hosted Agents API deployment or upgrade task.
The existing smoke script remains the actual candidate business check, but offline tests do
not establish it has passed on these new images. Partial destruction that removed the
Dispatcher requires independent cleanup confirmation before remaining resource deletion.
An uncertain publication is preserved for inspection and is not automatically replayed.
No new cloud resource, credential, package release or template qualification was created by
this child task. Generic build/deploy reuse and retained-native-auto accounting belong to the
CLI; its review findings were sent to that owner separately.
