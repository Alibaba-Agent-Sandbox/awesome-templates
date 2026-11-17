# Agents API template family — post-implementation review, round 1

Date: 2026-11-17. Reviewer: protocol_audit. Result: CHANGES REQUIRED.

## Reviewed scope

Read the six standalone `agents-api-{codex,qwen-code,claude-code,qoder,opencode,deepseek-harness}`
projects, family generator/tests, bootstrap/release scripts, native FC props, catalog,
engineering check metadata, shared protocol/Harness guides and contributor rules.
The review targets the current uncommitted candidate, based on template PR311
`ee59a726bb04e9b67a79b1bcbbb0a528ced11ef1`; it does not certify an image/cloud release.
The SDK source used for the following local cross-consumer probe is the current
six-Harness 0.4.0a8 candidate, installed editably in the dedicated environment.
No cloud resources or model requests were created by this review.

## Findings

### P1 — Missing model environment allowlist makes all six first inputs fail

`agents-api-codex/server/bootstrap.py::compile_environment()` compiles model bindings
but omits `modelEnvAllowlist`. `ManagedConfig` defaults it to an empty list. The actual
`ManagedExpressBackend.create()` compares the Session's frozen allowlist to its native
model environment and rejects the Session before provider I/O.

An executed six-profile probe used each project's own bootstrap, parsed its compiled
Worker config using the actual SDK, created a real managed logical Session in a local
SQLite database and called the real backend's `create()` with that frozen Session:

| Harness | Frozen allowlist | Actual result |
| --- | --- | --- |
| codex | `[]` | `ManagedError: model_env_not_allowed` |
| qwen-code | `[]` | `ManagedError: model_env_not_allowed` |
| claude-code | `[]` | `ManagedError: model_env_not_allowed` |
| qoder | `[]` | `ManagedError: model_env_not_allowed` |
| opencode | `[]` | `ManagedError: model_env_not_allowed` |
| deepseek-harness | `[]` | `ManagedError: model_env_not_allowed` |

The family test only constructed a backend; it never consumed a real Session. The
canonical release regression passed a hand-written Session with an allowlist, hiding
the integration gap. Fix the compiled config using only the selected Harness's known
native credential names, retain the SDK's fail-closed check, and regress the exact
bootstrap → config → Session → backend flow with provider I/O intercepted only after
admission and environment construction have actually run.

### P1 — Generated Guest Dockerfiles contain literal patch markers

The generator's npm RUN string contains `\n+    &&`. All six generated Dockerfiles
therefore contain a literal `+` token on continued shell lines. It becomes an extra
npm install argument and an extra version-probe argument, so these are not the
intended pinned installation commands. Remove the markers in the generator and
resynchronize. Add a regression for the generated installation command/argv; schema
validation and Python bootstrap tests do not execute a Dockerfile RUN.

### P2 — Non-Codex configuration documentation still requires Responses

The generated English READMEs for Qwen Code, Claude Code, Qoder, OpenCode and DeepSeek
Harness say that the provider must support real tool rounds through Responses. The
generator replaces `Responses API`, but the canonical sentence says `through Responses`,
so that replacement never applies. This directly contradicts the correct Harness table
and authentication mappings. Generate the complete protocol sentence from the profile
in both languages. For Qoder, explain its native service/PAT without inventing an OpenAI
endpoint. Distinguish public model ID from private credential/endpoint delivery.

### P2 — Source generation can copy ignored private overrides and retain obsolete files

`expected_files()` walks every regular file under the canonical directory, excluding
`.env` exactly but not `.env.local`/other `.env.*`, even though the recipe explicitly
ignores those private overrides. A maintainer running sync in a configured project can
copy such files into the five sibling projects. No secret was discovered or printed in
this review; this is a concrete source-selection flaw. Use a maintained source file set
or exclude all declared private patterns. `--check` also only compares expected files
and never reports unexpected obsolete generated source files, so removal upstream can
leave old executable helpers downstream. Add focused generation boundary regressions.

## Reasonable design retained

- A maintained canonical implementation with independently downloadable projects is
  appropriate. Runtime imports read local profile files; the downloaded projects do
  not import sibling recipes or depend on Registry metadata after initialization.
- Credentials use native Harness names. Gateway receives a business-key hash,
  Dispatcher owns routing/platform access, and only Worker gets model credentials.
  Instance model environment still needs the missing allowlist fixed above.
- The shared project protocol, explicit busy-session rejection, separate queue,
  immutable captured artifacts and close/delete distinction remain coherent.
- Native FC component props stay native. The release helper retains private
  ownership/revision/database identity and drain checks. Its documented uncertain
  publication limitation is honest; it is not automatic rollback.
- Existing provider fields and generation-2 profile were preserved. The anonymous
  provider ingress is still protected by the Gateway's application bearer token;
  the private Worker/Dispatcher remain signed invocation endpoints.

## Ingress and acceptance boundary

The helper publishes a candidate Gateway version, invokes its returned provider HTTP
URL for health/business checks, then switches the `prod` alias and stable trigger.
That is the intended single-endpoint topology. Actual provider URL routing, methods,
TLS, stable alias updates and live SSE behavior must be verified at FC; a local HTTP
listener does not establish those ingress semantics. The recipe uses an FC test URL,
not an automatically provisioned production domain. Documentation should continue to
make that distinction and should not equate durable replay with native token streaming.

The family currently pins client/server 0.4.0a8, explicitly not yet published. Both image
builds are therefore blocked at that dependency until a verified paired runtime release
exists. No source archive fallback should silently bypass this gate. Six directory
checks and local envelope tests cannot certify six Harnesses on Express or real model
continuation/tool/cancellation behavior. Retained-Session upgrade and independent owned
cleanup remain required before reporting this request fully complete.

## Action and follow-up

Root received each finding immediately and is repairing the generator/bootstrap and
adding cross-consumer regressions. This is the first requested post-implementation
review, not an approval. Round 2 must review the corrected files and actual evidence;
it must preserve missing release, image, cloud and model gates even if local tests pass.
