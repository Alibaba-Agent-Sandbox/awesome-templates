# agents-api-claude-code

## Purpose

Expose one stable Gateway for Claude Code in Session-owned Sandbox instances.
See the [Harness guide](../agents-api-harnesses.md), [shared API](../managed-agents-api.md)
and [native Harness source](https://code.claude.com/docs/en/headless).

## Capabilities

Every family member uses the same durable Session, Submission, events, file and
artifact contract. Native tool loops and authentication remain Harness-owned.
No steering, public function tools or remote MCP capability is implied.

## Exposed API

Business clients use the Gateway. The private guest bridge is never a generic
shell/files endpoint. `agents_version()` is a bounded local installation diagnostic.

## How to build

The standalone [recipe](../../agents-api-claude-code/template.yaml) prepares the Sandbox image and
three native FC roles. The Guest pins @anthropic-ai/claude-code 2.1.290.
Client/server0.4.0a8 is a release candidate dependency, not a published artifact.
The family generator copies shared release/bootstrap/smoke code into each project;
source acquisition never requires a sibling recipe at runtime.

## Express feasibility

Feasible: slice

Limiting factor: existing PostgreSQL, FC role, model/account entitlement and a
compatible paired runtime release. Cloud qualification requires new exact-source evidence.

## Risks

The Harness sees its selected model credential. Cloud/database and business keys
stay in Server roles. Receipts, runtime epochs, uncertain results, process cleanup,
revision pins and drain checks must remain intact. Raw Agent output is not an
independent attestation. Upstream license: Proprietary; the recipe itself is Apache-2.0.

## Test plan

Run strict template/catalog/docs checks and shared family/bootstrap regressions.
Build both non-root images with the published matching runtime. Run two dependent
real-model file tasks through the deployed Gateway, independently verify downloaded
source and unchanged original tests, retain a Session across an application upgrade,
then close/delete and independently verify owned resource removal. Local fixtures
cannot establish model, image or cloud acceptance.
