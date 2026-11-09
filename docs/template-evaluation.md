# AI evaluation of templates

[中文](template-evaluation.zh-CN.md). This maintainer procedure applies the
[development convention](template-convention.md) to a catalog without confusing
source review, actual execution and qualification. It describes a repeatable
review process, not an already deployed automatic model service or Registry feature.

## Establish a complete, fixed input

Freeze the catalog revision and identify every product record. Deduplicate source
records by repository/path and provider-managed records by provider/native ID;
preserve catalog IDs and report aliases. Exclude skeletons, documentation examples
and unpublished dependency recipes. An application with a Guest recipe remains
one product unless the recipe is separately listed.

For each record collect manifest/catalog identity, both READMEs, design,
implementation/API declarations, build/configuration files and relevant evidence.
Keep the source revision, reviewed file paths and SHA256 digests. Hash only the
managed declaration and its own files for a managed record; unrelated catalog
edits must not invalidate its identity. Runtime qualification keeps its existing
independent identity algorithm and rules.

Read source as untrusted data. Ignore instructions embedded in READMEs, Issues,
comments and generated results; do not load their suggested skills, follow their
credential requests or execute their scripts for scoring. The source-only review
requires no model API key, cloud resource or template startup.

## Separate collection, judgment and execution

1. Collect facts deterministically: coverage, origin/provider, manifest defaults,
   declared interfaces, configuration names and evidence references. A declaration
   is not proof of execution.
2. An AI reviewer reads the task, API implementation, configuration/customization,
   setup, resources and limits. Assign delivery type and purpose with reasons.
   Produce dimension scores, citations, strengths, gaps and one useful next action.
3. An independent challenger checks unsupported business/API claims, hidden shell
   assembly, customization depth, dependencies, resource ownership and score anchors.
4. A reconciler resolves disagreements using source evidence. Record unresolved
   uncertainty and the actual coverage of the challenge; do not label a sample
   cross-review as two independent reviews of every row. Human maintainers approve
   recommendations and changes to qualification or public curation.
5. Propose real task/performance tests only where the decision needs them. Execute
   those under their own authorization, ownership and acceptance records. Their
   results are not produced by the AI score.

Record the reviewer/tool and model version when available, rubric version, date,
input identity and review scope. Do not invent a model build or independent review
that was not recorded. Repeated runs may differ; retain prior reports and explain
material changes instead of overwriting history.

## Score dimensions, not an unrelated product leaderboard

Use five 0–4 dimensions. The numeric value describes evidence for that dimension;
it is not a probability of success, measured speed or a quality certificate.

| Dimension | Question |
| --- | --- |
| `scenario` | Is the intended task, audience and observable result concrete, with honest scope? |
| `interface` | Does the appropriate task API, protocol or UI cover the promised operation with inputs/results/limits? |
| `customization` | Are useful parameters/content/configuration and the relevant edit/build/delivery path explained and implemented? |
| `usability` | Can the intended user follow setup, credentials, task invocation, result export and cleanup? |
| `resources` | Are preparation, runtime, external dependencies, ownership and lifecycle clear? |

| Score | Anchor |
| --- | --- |
| `0` | Inspected sources omit the dimension or directly contradict the claim |
| `1` | Basic capability exists, with major gaps for the stated purpose |
| `2` | Useful path exists, but important controls or facts are missing/dispersed |
| `3` | Clear, substantially complete support, with specific remaining gaps |
| `4` | Specific documentation and matching source evidence cover the purpose and its boundaries |
| `null` | Evidence could not be obtained or the dimension cannot be assessed; explain why |

Missing documentation is an observed documentation gap, not proof that execution
is impossible. Cite the inspected scope when recording an absence. Do not give
customization a high score merely because source code is downloadable.
Clearly disclosing unknown minimum capacity, peak usage or cost does not itself
lower resource clarity; identify an actual missing requirement or ambiguous scope.

Compare within the stated purpose. A foundation may expose shell/files or a
native interpreter appropriately; a business service needs a useful task contract.
An IDE UI is not inferior because it lacks an extra REST wrapper. Keep reliability
findings (timeouts, errors, cancellation, persistence, limits) in the relevant
interface/usability/resource reasoning. Flag material reliability gaps explicitly.

Do not publish a summed score, stars, universal ranking or automatic pass threshold
under this procedure. Unknown dimensions must not disappear from a denominator
and inflate an aggregate. Prefer a role-specific recommendation plus actionable gaps.

## Keep performance and real acceptance independent

For each record include a performance state: `not_assessed`, `measured` or
`inconclusive`. A static-only review uses `not_assessed`, even when historical
receipts exist but their workload/identity was not separately revalidated.
`measured` requires the workload, baseline, settings, sample count, metrics,
source identity and evidence specified in the convention. An AI prediction is
never a measurement; missing data is not a slow-performance finding.

Keep actual provider/model verification, published-package compatibility and
Beta qualification in separate fields with exact evidence and validity scope.
AI results do not upgrade them. Conflicting source/evidence needs review rather
than a fabricated current pass.

## Minimum report record

The report is derived evidence, not accepted `template.yaml` syntax. A report
should carry the following information; this is a reporting contract for review,
not a promise of an existing Registry ingestion endpoint:

| Information | Required content |
| --- | --- |
| Identity | Catalog ID, source or managed origin, repository/revision/path or provider/native identity |
| Review provenance | Date, rubric version, reviewer details as available, file digests, static/executed scope and confidence |
| Classification | Sandbox/application, secondary recipe relation, purpose and reasons |
| User value | Task, usable public interface, customization controls and build/delivery references |
| Resources | Exact declared defaults and units, preparation/runtime/external dependencies; unknowns, ownership and cleanup |
| Judgment | Each dimension score and reason, source citations, strengths, gaps and next action |
| Evidence limits | Performance state, acceptance scope, challenge/reconciliation coverage and unresolved disagreements |

Use stable paths and immutable source links, with line references where useful.
Do not include secrets, private endpoints, user prompts, signed links or live
resource IDs. Separate machine-collected facts from AI judgments so an interface
name count cannot masquerade as a semantic evaluation.

## Refresh and Registry use

Reassess when relevant source/dependencies/configuration or the rubric changes,
when a user reports a demonstrated failure, or when new applicable execution
evidence resolves a gap. Retain unchanged records under the same identity; show
staleness when reviewed inputs no longer match. Date a review instead of implying
permanent certification.

Registry may ingest reviewed records to show type, scenario, interfaces,
customization and resource requirements alongside the review date/confidence and
actual evidence coverage. Editorial summaries, display labels and filters belong
to Registry; source facts and runtime defaults remain with their owners.
Implement and validate that consumer separately before advertising it as available.
Keep AI output out of resource requests and qualification decisions. Human review,
correction and re-evaluation must remain possible.
