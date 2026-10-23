# Project standards and definition of done

This document governs repository maintenance. The [template specification](template-spec.md)
governs template contracts; the [documentation standard](documentation-standards.md)
governs explanations and examples. [中文](project-standards.zh-CN.md).
An experiment, a merged implementation and a verified provider deployment are distinct states.

## Ownership and sources of truth

| Artifact | Authority |
| --- | --- |
| Template implementation | Its root directory, manifest, Dockerfile and named commands |
| Public catalog | `awesome-templates.yaml`; one entry per installable template |
| Runtime/API contract | Public Python SDK/server source, linked at an exact revision in evidence |
| CLI behavior | Actual CLI help and source at the tested revision |
| Acceptance | Current template-local receipts and their repository engineering summaries |
| Roadmap | GitHub Issues; the dated market survey is research, not implementation status |
| Website/catalog rendering | The independently maintained registry repository |

Use absolute GitHub links across repositories. Do not introduce a sibling-checkout
dependency, copy registry output here, or change SDK/CLI contracts from a template.
Read `AGENTS.md`, `CONTRIBUTING.md`, template-local instructions and the matching
design before editing. Inspect the existing diff; isolate overlapping work.

## Design and implementation

Every template needs a concrete user task, pinned upstream source and license,
named-command schema, resources, feasibility decision and executable test plan in
`docs/design/<name>.md`. State whether Express supports the full product or a
specific slice. A remote service client does not establish that the remote
service runs inside Express. Document missing hardware, accounts, licenses,
datasets and external services instead of substituting a similarly named tool.

Start from `_skeleton/`. Preserve the default Express recipe's platform base, generation, readiness,
non-root runtime, reserved ports and `agent_sandbox.server` contract. Declare
provided services and explicit workflow requirements. Additional explicit build profiles follow
[the workflow rules](workflows.md#explicit-build-profiles), preserving the original recipe. Validate arguments and bound input/output sizes,
execution time and subprocesses. Pass user input as argv, preserve nonzero exits
as errors, and clean up owned descendants on completion, failure and timeout.
Inspection commands must not silently alter configuration. Isolate generated
workspaces and preserve caller files, unrelated processes and original tests.

Keep dependencies reproducible: exact versions or immutable source commits,
available lockfiles, integrity hashes for downloaded assets where supplied by
upstream, and explicit install/build commands. Never claim that a package is
published because a package name exists. Record package and source versions.
For a dependency update, recheck architecture, platform compatibility, license,
installed version, command flags and affected runtime tests.

## Code conventions

Use the existing Python style: four-space indentation, descriptive snake_case
functions, explicit public signatures/types and JSON-serializable command results.
Keep imports free of server startup and cloud mutation. Separate argument validation,
upstream execution and artifact verification. Catch errors only where the code can
recover or produce a stable sanitized contract; never turn execution failure into
a successful string. Standalone templates stay independent of sibling folders.
Use existing checker/test tooling. Introduce a formatter/linter only as a scoped
repository decision; do not reformat unrelated files.

## Public compatibility and versioning

The manifest version describes the template contract. Change it when runtime
behavior, dependencies, defaults, arguments or resources change. Explain removed
or renamed commands, stricter validation and changed permissions in both README
languages; document a migration for incompatible changes. Keep manifest,
catalog, command reference, design and examples consistent. A previous version's
provider receipt cannot certify a changed template. Preserve it as dated history.

## Security, licenses and resource ownership

Keep `LICENSE`, `NOTICE` and upstream attribution. Identify redistributed source,
assets and model/data licenses in the design and README. Do not include restricted
artifacts without redistribution rights. Treat inputs and generated agent code as
untrusted; permission bypass requires an explicit documented option.

Declare secret names with empty manifest values; inject values through the
documented process environment. Never commit `.env`, credentials, private URLs,
raw provider/model logs or resource identifiers. Do not send Express credentials
to another provider. A cloud run authorizes its required API calls; copying
credentials into Actions or another service requires separate authorization.
Report vulnerabilities privately using the repository's enabled GitHub private
reporting route. If unavailable, request a private contact using a nonsensitive
Issue; do not publish exploit details or secrets.

Record unique ownership before creating cloud resources. Reconcile ambiguous
responses using exact identifiers and aliases. Verify absence independently
after deletion. Cleanup uncertainty is a failure/blocker, never a pass. Only
delete resources created by that run. Document TTL, cancellation limitations,
retention and any remaining private recovery journal.

## Validation and evidence

Run the checks relevant to the changed behavior and all applicable CI gates.
The repository workflow files define the executable CI commands. Use the
existing regression suites; add a behavior regression for a bug fix that fails
before the fix and passes after it. Mocks prove the controller behavior only.

| Change | Required verification |
| --- | --- |
| Documentation | Local links, examples, translations, engineering record and diff checks |
| Specification/checker/catalog | `python scripts/test_spec_tools.py` and `python scripts/check_template.py --all` plus targeted regressions |
| Runtime or dependency | Relevant unit/process tests and L0; image build/pin checks for image changes |
| Provider claim | Real deployment, external CLI/SDK smoke and independent owned cleanup at the exact revision |
| Coding/model claim | Strict real-model source edit, new artifact, unchanged original tests and independent held-out assertions |

L0–L4 remain as defined in the specification. A platform-step run records its
build mode; it cannot establish that a Dockerfile was built. Source-runtime
success cannot establish image deployment. Missing keys and skipped tests remain
explicit. For every changed repository, include an English seven-section decision
and dated evidence under `.agents/`; link template-local receipts. Evidence states
PASS, PARTIAL, FAIL or BLOCKED, exact scope/hashes, tool versions, actual commands,
counts, limitations and cleanup. Never overwrite merged historical evidence.

## Issues, review and delivery

Reuse the matching Issue and enumerate its acceptance criteria. Record a
reproducible defect separately from a hypothesis. For a broad roadmap request,
track design, implementation, local, image, Express, model, documentation and merge
criteria independently. A new directory or experimental PR does not close a
request that also requires real deployment. An infeasible-product decision only
closes an Issue when the Issue explicitly accepts that outcome and evidence is
complete. Keep external blockers and missing operator inputs visible.

Commit scoped changes with Conventional Commits. Use the repository PR template,
link the Issue and summarize behavior, validation and material limitations. Push
a task branch, inspect checks/reviews for its latest head, and resolve feedback.
Merge only through a permitted method after applicable checks and required review
pass; never bypass protection, force shared history or push to main. Confirm
remote MERGED state, linked-Issue criteria and post-merge checks.

Catalog qualification and package publication are separate from merging. Never
invent tags, package releases or registry publication. Release/tag operations
need authorized scope, compatibility notes and verified artifacts; example install
references must resolve to an actual published commit or tag.

## Definition of done

- The requested behavior and every linked acceptance criterion are implemented,
  or an explicitly accepted evidence-backed feasibility decision is delivered.
- The template, catalog, bilingual docs, design and contract versions agree.
- Required regressions and current-head CI pass; required real Express/model
  checks have receipts, exact provenance and independently confirmed cleanup.
- Licenses and attribution are retained; scoped diff and configured-secret checks pass.
- Engineering note and evidence are included and indexed; failures/skips remain explicit.
- The scoped PR is actually merged and Issues close only when all their criteria hold.

If any required item is blocked, report the concrete missing prerequisite and
the reviewable work completed. Do not describe partial implementation as done.

For pip hash-lock installation, use --require-hashes -r with one explicitly copied local lockfile. Each requirement must use an exact version and SHA256; do not mix additional unpinned package arguments or external requirement/index directives. The checker supports simple COPY source-to-file mappings; image pip enforcement and pip check remain required.


A template requiring a newer server contract may add `server-sdk.commit` with one
lowercase40-character public commit and a newline. It must agree with its immutable
Dockerfile server fallback. L1 checks out that source before building the wheel;
archive and registration proof checks select the same pin. The opt-in file is part
of the hashed context. Templates without it retain the historical common injected
pin, so adding one consumer does not requalify or change other runtimes.

The default Dockerfile server archive must match `scripts/server_sdk_pin.py` (or the explicit `server-sdk.commit`). The checker rejects a different fallback, so default and CI-injected builds select the same server source. Changing a pin invalidates prior source-specific image/workflow acceptance; preserve those receipts as history.
