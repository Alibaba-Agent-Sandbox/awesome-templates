# Template development convention

[中文](template-convention.zh-CN.md). This contributor convention defines useful
template design. Read it with the [executable manifest specification](template-spec.md),
[project standards](project-standards.md) and [documentation standard](documentation-standards.md).
It adds authoring and review guidance; it does not introduce manifest keys,
new CLI commands, automatic qualification or a new runtime protocol.

## What makes a good template

A good template helps a stated audience complete a useful task with a predictable
result, exposes the controls needed to adapt that task, and explains what it
costs to prepare, run and remove. Installing software is useful infrastructure,
but is not evidence of an out-of-the-box business workflow.

Authors must describe one complete path: **input → operation → observable result
→ export or continued use → cleanup**. Name the supported scope and the work
left to the caller. Do not describe a benchmark slice as the complete upstream
product, or a developer building block as a finished business application.

## Describe delivery type and origin separately

| Delivery type | What users receive | Required description |
| --- | --- | --- |
| Sandbox template | An instance with tools, files, a runtime or task services | How to create/connect, invoke its useful interface, export results and release the instance |
| Application template | A deployable service that manages its Sandbox usage | Its business entry point, application configuration/deployment, state, Sandbox ownership, result access and removal |

An application may also build a Sandbox template. Describe that dependency;
do not count it as a second catalog product unless separately published.
An HTTP server inside a Sandbox is still a Sandbox template when callers manage
and address the instance. A stable external business endpoint is part of the
managed application experience, not something every Sandbox building block needs.

Origin is a separate attribute: source-built or provider-managed. Preserve the
provider and native identity of a managed runtime. Existing catalog maintenance
labels and Beta/provider qualification remain separate from both delivery type
and AI review. Do not reinterpret an existing catalog `kind` field as delivery type.

State the intended role as well: foundation/toolchain, task service, Agent
runtime, development service or benchmark. Review against that role. A browser
with CDP, an interpreter or an IDE can be a good foundation without pretending to
provide a complete business workflow.

## Provide the right interface

For a task or business service, users should supply task inputs rather than
assemble installation, shell quoting, process supervision and output parsing.
Document these contracts:

- Typed inputs, required/default values, limits, supported files and permitted side effects.
- Useful structured outputs or downloadable artifacts; how to inspect success independently.
- Validation and execution errors, authentication, status and retry semantics.
- Buffered versus streaming results, execution deadline, cancellation and retained state.
- A complete example through each applicable supported entry point, using the same task.

Use the existing server SDK named-command interface where appropriate.
`abx run <id> <name>` and `client.commands.run(...)` call a registered HTTP
operation. `abx exec` and `sb.commands.run(...)` execute processes. Judge the
operation's contract, not the word `run`.

| Shape | Review conclusion |
| --- | --- |
| `execute(command: str)` accepting arbitrary shell text | A process transport; it does not itself provide a business task API |
| Document conversion with input/format/deadline, output path/bytes/hash and explicit errors | A meaningful task interface, even when its implementation invokes Pandoc |
| Agent task with workspace/files/model controls and result/status/artifact access | An adaptable Agent interface when the documented controls are implemented |
| IDE browser UI, CDP or another suitable native protocol | A valid interface for that purpose; an extra REST wrapper is not inherently useful |
| Version/health only | Diagnostics; insufficient evidence that the claimed task works |

Raw process execution may remain available for advanced use. It should not be the
only usable path for the business capability advertised as ready to use.
Application clients should use the documented service endpoint without learning
individual Sandbox addresses or handling provider management credentials.

## Make customization useful and repeatable

Explain the supported customization levels; use only levels that actually exist:

| Level | Author must show |
| --- | --- |
| Task parameters | Change inputs, output formats, workspaces, budgets or task options |
| Configuration/content | Change applicable prompts, model/endpoint, tools/skills, policies, workflow content, files or dependencies |
| Source extension | Identify the files and extension points to edit, including constraints and compatibility |
| Build and delivery | Build/launch the edited Sandbox source, or build/deploy the edited application, using existing supported tooling |

Include one meaningful modification and its resulting behavior. State which
changes require restart/rebuild/redeploy and what persists across updates.
Changing only a software version or pointing at a repository is not a complete
customization guide. Do not promise arbitrary workflow or model support for a
specialized template. Preserve the distinction between client timeout and task
deadline, and between closing a local client and deleting a remote resource.

Keep consumer configuration and practical extension instructions in the
appropriate guide/design/contributor location; link them from the template.
Use actual configuration names. Explain each credential's purpose, source and
injection path without exposing values. Normal CLI setup should generate/save
the default application token using the existing supported flow; advanced custom
tokens and external clients need their own instructions. Application tokens,
Sandbox API credentials, cloud AK/STS and model keys serve different purposes.

## Declare the complete resource footprint

The manifest's Sandbox CPU/memory request is not the application's total cost.
Document the following groups in the template's resource/configuration guidance:

| Group | Information to provide |
| --- | --- |
| Preparation | Host OS/architecture, build tools or Docker when needed, artifact/image registry, build disk and deployment permissions |
| Runtime | Sandbox CPU/memory and units, disk needs, GPU/privileges if required, ports, lifecycle, workspace persistence and concurrency |
| External services | Required/optional model account, PostgreSQL/storage, FC/SAE or other serving, network/VPC/TLS, datasets and licenses as applicable |
| Ownership and removal | Who provisions/pays, created versus borrowed resources, retention/TTL, result export, normal deletion and failed-run recovery |

For each resource state **required or optional**, **created by the deployment or
supplied by the user**, its configuration/reference source and its cleanup owner.
Say explicitly when a dependency must already exist; do not imply automatic
database provisioning because a binding is present.

Distinguish configured defaults, a verified minimum and measured usage. If a
minimum or measured peak is unknown, say so. Do not infer disk, GPU, regional
availability, currency prices or capacity from a CPU/memory declaration.
Express memory units and provider constraints must follow the actual manifest
and provider contract; do not silently relabel MB as MiB. Explain per-instance
or per-active-Session multiplication and any independently provisioned server
resources. Include billing categories rather than unsupported cost estimates.

For example, [agents-api](../agents-api/README.md) needs a Guest Sandbox for each
active Session, Server FC roles, existing PostgreSQL, image storage and model
access. Its root resource block describes the Guest. By comparison,
[document-tools](../document-tools/README.md) supplies bounded local conversion
without a model account. Their resource descriptions should reflect those
different dependencies.

## Treat performance as a measured property

An API can reduce integration effort without reducing computation or latency.
Process-per-call and resident services have different startup, memory and
concurrency tradeoffs. Identify expensive stages before choosing the design.

A performance claim needs a reproducible workload and baseline, exact template
and dependency versions, provider/region/resource settings, input size, sample
count, cold/warm distinction and concurrency. Report the applicable startup or
first-result latency, end-to-end latency distribution, throughput, failures and
resource consumption. Include model/network variability and known limits.
Keep the measurement and raw sanitized evidence in engineering records; user
docs may state the resulting supported limit with a link to its evidence.

Without those measurements, label performance unmeasured. Do not convert a
successful health request or an AI opinion into a benchmark. A current absence
of measurements is a gap to investigate, not proof that a template is slow.

## Acceptance and maintenance

Use the existing [definition of done](project-standards.md#definition-of-done)
and [verification levels](template-spec.md#test-levels). A task example must
check the actual result; coding tasks need independently checked files/tests,
not only a model response marker. Preserve failed attempts and exact version
scope. Do not repeat paid cloud runs merely to populate an AI assessment.

For new templates and changes to a claimed capability, review the task,
interface, customization, resources and lifecycle together. Existing templates
receive explicit improvement findings; this convention does not silently change
their runtime schema, hide them or promote their qualification. Fix demonstrated
gaps in scoped changes with the appropriate regression and usage updates.

## Template facts, AI results and Registry presentation

| Owner | Authoritative content |
| --- | --- |
| Template source | Executed manifest, implementation, task/API/configuration, customization and resource facts |
| Engineering evidence | Revision-bound static assessments, provider/model results, performance measurements and cleanup evidence |
| Registry | Display categories, translations/summaries, filters, recommendation text and presentation of cited evidence |

Registry should show delivery type/origin, scenario, usable interfaces,
customization level, preparation/runtime/external dependencies and whether a
statement is an author declaration, static review or actual execution result.
AI assessments are derived review data, separate from author-supplied facts.
They must not overwrite native identities, runtime requests or Beta eligibility.

Pure display/editorial information belongs in a separately reviewed catalog or
Registry presentation contract, not in execution YAML by default. This convention
does not define new accepted metadata fields or claim Registry already renders
them. Any machine-readable ingestion change needs a consumer, versioning,
validation and migration in the owning repositories.

Use the [AI evaluation procedure](template-evaluation.md) for a whole-catalog
assessment. Its findings support review and improvement; they are not certification.
