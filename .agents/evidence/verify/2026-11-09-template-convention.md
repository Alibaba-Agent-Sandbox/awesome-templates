# Template convention and all-catalog static review

Date: 2026-11-09. Result: PASS for the local documentation and assessment checks
listed here. Remote current-head CI and PR merge are separate delivery gates,
recorded on the PR; this file does not assert a remote merge or runtime pass.

## Scope and baseline

Product source baseline: `e94ab308a74715982bb059b142518f7d6070c1c2`.
Scoped changes: bilingual convention and AI procedure, CONTRIBUTING/README entry
links, this repository's decision/index/evidence and derived assessment JSON.
No manifest, catalog declaration, runtime, dependency pin, CLI/SDK behavior or
qualification rule changes. The older workspace checkout and unrelated existing
engineering edits were left intact; work used a separate branch/worktree.

Python 3.13.13 with the repository's `scripts/requirements-spec.txt`
(`PyYAML==6.0.3`, `jsonschema==4.26.0`). No template code, cloud/model task,
database provisioning, resource deletion or package release was needed.

## Design review and actual AI coverage

Independent design review supported purpose-aware guidance, meaningful task APIs,
customization through delivery, three resource groups and separation of Registry
presentation from executable configuration. Foundation/IDE/CDP/benchmark value is
preserved. API presence does not establish better performance.

Three collaborating AI reviewers partitioned the 51 semantic initial reviews:
21 records (17 source plus four managed), 15 source and 15 source. Each read the
applicable task/configuration/resources/API documentation, manifest and core
implementation declarations. The root reconciler inspected combined findings,
relevant source samples and score anchors. Two independent challengers sampled
eight rows: agents-api, code-server, desktop, codex-agent-api,
code-interpreter-v1, document-tools, hermes-agent and next-app. They also reviewed
the bilingual convention/procedure. This is **not** two independent reviews of
every catalog row. Exact model build was unavailable; no model identity is invented.
No human maintainer approval of the per-template judgments is recorded.

The [assessment](2026-11-09-template-convention-assessment.json) includes all
47 source and four managed catalog records, with no skeleton/example duplication.
One primary application (`agents-api`) also prepares its Guest recipe; the other
50 records have primary Sandbox delivery. Source/managed origin remains separate.
There are five evidence dimensions and no aggregate or universal ranking.
All performance states are `not_assessed`; runtime acceptance is `not_reassessed`;
qualification remains unchanged. Reviewed-file hashes bind each row to its input.
Managed records hash their own canonical catalog declaration, not the whole index.
This review identity does not replace the qualification identity algorithm.

### Reconciled findings

- Generic coding examples are concrete Agent-runtime tasks. Industry-specific
  depth is an enhancement; twelve scenario scores were calibrated from 2 to 3.
- Codex and agents-api have useful configuration controls, but no complete
  content/source extension-and-delivery example in inspected instructions;
  customization scores were calibrated from 4 to 3.
- Unknown measured minima or usage do not themselves reduce resource clarity.
  Five initial resource scores were raised from 2 to 3; document-tools was raised
  from 3 to 4 for its documented defaults, bounds, dependency and ownership scope.
  Hermes resource clarity was raised to 3; its detached accepted-turn cancellation
  limitation remains a distinct interface/lifecycle finding. Next-app remains 3
  with a clarified provider scope finding rather than a missing-benchmark penalty.
- agents-api resources were calibrated from 4 to 3: its README says MiB while the
  normative root manifest memory field is MB; Guest defaults also do not disclose
  Server/database sizes. Preserve the inconsistency rather than silently converting.
- Sandbox templates do not inherently need a cross-instance Gateway or an
  industry-specific schema. Some initial observations concern optional extension
  opportunities or scope limits, not defects; the report explicitly retains that
  interpretation boundary. No follow-up runtime change is implied by an observation.
- A final independent challenge corrected a Prime Agent initial statement about
  caller-prepared kernel dependencies: the Dockerfile already installs/checks
  them. Its usability score remains 3 for documented setup/deadline complexity.
  Manual-token findings describe README instructions, not tested CLI inability.

The 46 source Sandbox templates already declare typed named-command transport.
`abx run` is not itself proof of arbitrary shell-only design. Managed desktop
examples do not demonstrate the main screenshot/input path; the Express managed
interpreter documentation warns about exception-triggered repeated side effects.
These are source/document findings, not new backend reproductions.

## Executed checks

| Check | Actual result |
| --- | --- |
| `python scripts/check_docs.py` | PASS: 236 current public documents, zero local link failures |
| `python scripts/check_docs.py` with the three changed Markdown engineering records | PASS: three records, zero local link failures |
| `python scripts/test_spec_tools.py` | PASS: 52 tests; negative fixtures intentionally print conformance failures before suite success |
| `python scripts/check_template.py --all` | PASS: 48 conformant directories including skeleton; no claimed-spec failures |
| Assessment coverage/identity checks | PASS: 51 unique catalog records, exact source/managed sets, complete five-axis reasons and source references |
| Evidence-reference checks | PASS: 611 dimension citations resolve to existing fixed-source file/line pairs |
| Reviewed inputs | PASS: 393 file-digest records; own catalog declaration digests kept separately |
| Score/state checks | PASS: scores in 0..4 or explicit unknown; no sum; all performance unassessed and qualification unchanged |
| Translation and challenge | PASS: English/Chinese authoring rules agree; reviewer translations preserve scores and citation paths; root reconciliations remain explicit |
| `git diff --check` | PASS |

The first report assembly attempt rejected a managed README file path mistakenly
treated as a directory. Correcting the assembly path handling produced the complete
report; no template or catalog source was modified by the failed attempt.
Local link/spec checks are not image/cloud/model/performance acceptance.
No new behavioral tests were introduced for this documentation/evidence change.

## Prior managed Agents delivery status

Fresh remote metadata confirms [template PR296](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/296),
[Python PR156](https://github.com/Alibaba-Agent-Sandbox/python-sdk/pull/156),
[CLI PR238](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/pull/238) and
[article PR33](https://github.com/Alibaba-Agent-Sandbox/blogs/pull/33) merged.
The public article returned HTTP 200 during this read-only audit.
The final version0.1.4 public recipe uses CLI0.5.10 and client/server0.4.0a7.
[Final immutable evidence](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/blob/e94ab308a74715982bb059b142518f7d6070c1c2/.agents/evidence/verify/2026-11-06-managed-agents-cli0510-prerequisite.md)
records normal Build/Plan/Apply, two real Qwen file turns through one Gateway,
download assertions, Close/Delete and independently confirmed owned cleanup.
The [published article](https://www.agent-sandbox.cn/blog/managed-agents-one-endpoint/)
contains the reusable user workflow.

Those records support the user's narrowed core task, not current complete
API/SSE/cancel/Codex/upgrade or performance coverage. Beta remains appropriate.
The five known temporary RDS instances and other known owned resources were
recorded released in that prior task; this audit is not a fresh account-wide
resource inventory. Older generic draft PR81/75 do not negate the shipped managed
profile. No further CLI/SDK release is needed for this convention and static review.

## Limitations and cleanup

The first assessment is derived review data, not an installed evaluator service,
Registry ingestion/rendering implementation or human-approved certification.
Registry-specific display fields and future filters need a scoped consumer change.
No new external link hosts were introduced by the contributor guide navigation;
immutable evidence links use freshly verified repository files.
All temporary work in this task is local. No paid/cloud resources were created.
