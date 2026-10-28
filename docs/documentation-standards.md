# Documentation standard

This standard applies to user guides, template READMEs, design documents,
contribution instructions and new engineering records. [中文](documentation-standards.zh-CN.md).
The [template specification](template-spec.md) owns exact README/design headings.

## Audience, location and authority

Write the task and observable result first. Put reusable usage in `docs/`,
template-specific arguments in that template's README, design rationale in
`docs/design/`, and executed verification in `.agents/` or template-local evidence.
Keep internal implementation details, validation matrices, pass/fail totals, frozen batches, repair progress and test-tier narratives out of the repository README, template READMEs and user guides. Keep engineering decisions and executed verification under `.agents/` or existing template-local evidence. Public documentation explains setup, supported behavior, actionable limits and cleanup; it does not reproduce internal reports. Maintainer instructions belong in contributor or engineering documentation. Link to the authority rather than copying contracts that will drift. Separate
current instructions from dated research and historical verification. Date
availability/feasibility observations and link the source or executed check.

## Languages and structure

Every template has `README.md` and `README.zh-CN.md`, using the exact ordered
headings in the spec. Shared normative project/documentation/step guides have
English and Chinese counterparts with reciprocal links. Update both in the same
PR when behavior, arguments, setup, limits or acceptance wording changes. English
is authoritative where the spec says so. Keep code identifiers, provider IDs,
command names, units and error codes identical across translations.

Use one H1, descriptive headings, short paragraphs, tables for parallel contracts
and fenced code with a language. Explain every placeholder before use. Distinguish
required, optional and default values, including units and supported ranges.
Avoid absolute workstation paths, undocumented aliases and examples that require
another repository beside this one. Cross-repository links use absolute GitHub URLs.

## Runnable examples and API reference

Every template documents the same useful task through CLI, Python SDK and HTTP
POST. Include installation provenance, provider setup, deploy/create, command
discovery, arguments, expected response and owned cleanup. Use commands verified
against actual help/source. Record whether examples were executed or only syntax checked in the engineering verification record. Do not imply a snippet is a real cloud pass.

Before launch, show required configuration with actual names and defaults: separate platform credentials, application tokens and model credentials. Explain the model ID, endpoint, API key and any product login required by the pinned upstream tool. State supported authentication and endpoint restrictions rather than mapping every tool to common environment variables.

Name the client distribution `agent-sandbox-client`, import the SDK entry point
appropriate to the pinned version, and install `agent-sandbox-server` inside the
image. Give a pinned source alternative when a package is unpublished. Keep typed
JSON arguments distinct from string CLI arguments. HTTP examples include method,
route, headers, direct argument object, result envelope, errors and authentication.

Command references document each parameter's type, required/default value,
constraints, output schema and side effects. Explain buffering/streaming, execution
deadline versus client HTTP timeout, cancellation behavior and process ownership.
Document configuration precedence and settings captured at process start; link
the [prewarmed-server guide](runtime-environment.md). A create-time environment
does not prove that an existing server process was reconfigured.

## Claims, limitations and safety

Publish only facts supported by code, primary upstream documentation or actual
execution. State full product versus supported slice. A capability declaration,
successful install, model marker, mock or green configuration job does not prove
the upstream product works. Workflow verification requires complete matching receipts and independently trusted CI provenance; preserve historical records.

Use placeholder secret names and values. Never include credentials, private
endpoints, resource IDs, signed URLs, private prompts or raw sensitive logs.
Show environment injection without embedding secret values in shell arguments.
Document permissions, writable paths, resource costs and cleanup when they affect
the user's operation. Never invent provider endpoints or authentication headers.

## Links, maintenance and review

Relative links resolve from the containing document. Check files and fragments;
avoid empty links and references to deleted files. Links inside examples must be
identified as placeholders. External links are checked when introduced or changed;
prefer official upstream docs and immutable source permalinks for technical claims.
Network errors and gated sites are recorded separately from successful checks.

Run `python scripts/check_docs.py` for local Markdown targets. Run scoped Python
example syntax checks when editing examples, and the strict template checker for
README/schema changes. Document/link checks do not authorize or run cloud tests.
Review translations, output examples, links and dates together. Update navigation
and CONTRIBUTING when adding a shared guide. Each docs change includes its own
engineering note and verification evidence, even if no runtime code changes.
