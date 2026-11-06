# Verification: published CLI0.5.10 deployment prerequisite

- Date: 2026-11-06
- Change: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/295 and https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/296.
- Result: PASS for the scoped core delivery — formal CLI, local checks, normal public0.1.4 deployment, two real Agent file turns and independent owned cleanup pass. Beta and wider compatibility limits remain.
- Recipe baseline: a4d43370ff82e244c542412d0af0c68759d19fdb, version0.1.3.
- Published CLI:0.5.10, source2f84e3f802e5f6abd98a528c457b844a9307041d; https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/releases/tag/v0.5.10.

## Dependency and identity

Independent official npm readback and fresh installation confirm version0.5.10,
installation exit0, actual artifact-check exit0, verified public metadata/tarball/
integrity and697 of697 installed dist files byte-identical to the reviewed
candidate, with no changed or extra files. The independent version command
returns `abx, version 0.5.10`. The public-readiness projection SHA is
604918ced52d6f5c0dfc0f17c8fb57e6bb7a3df462e70812a779face5505a246.
These release facts do not establish this template's hosted acceptance.

The two user READMEs now require the npm CLI0.5.10 with Node20+. Version0.1.4
records the deployment dependency change under the project public compatibility
rule. The image pins remain published SDK0.4.0a7; business HTTP callers still
need only the Gateway endpoint and business key. Both Dockerfiles, the smoke,
API, model prompts and runtime budgets are unchanged. Previous recipe identities
and failed public updates remain historical and are not relabeled.

## Local checks

Executed with the existing engineering environment and the repository's pinned
specification dependencies:

```bash
python -m pytest agents-api/test_smoke.py -q
python scripts/test_spec_tools.py
python scripts/check_template.py --all
python scripts/check_docs.py
git diff --check
```

| Check | Actual result |
| --- | --- |
| Existing smoke regressions |20 passed/4.85s |
| Specification/tool suite |52 tests/16.157s/OK |
| Whole manifest checker |48 conformant/0 failures |
| Markdown link checker |232 documents/0 failures |
| Diff whitespace and recipe delta |Passed; only the two READMEs and version field differ among the14 recipe files |

The first attempted run used the public runtime-only virtual environment rather
than the engineering environment; it lacked pytest and jsonschema. Smoke exited1
for missing pytest, while spec/manifest checks rejected the missing pinned
jsonschema dependency. These setup failures are retained as such; no assertion
or product file was changed to bypass them. The unchanged checks then passed in
the existing engineering environment. Pytest's fixture-loop-scope deprecation
warning is nonfatal and was not hidden by changing unrelated configuration.

Both an independent deployment reviewer and parent reviewed the exact dependency
change with no must-fix. The published CLI proof and version output were read
independently before modifying the public installation commands.

## Core hosted workflow and cleanup

The user explicitly narrowed final delivery to one Server Gateway endpoint with
the Agent executing in an owned Sandbox, its related real file workflow, a
detailed practical article and release of temporary resources. No additional
version, cross-repository publication, API/upgrade qualification matrix or
new cloud validation is required for this scoped delivery. Historical broader
evidence remains at its recorded identity and is not relabeled. Beta remains.

The exact14 recipe files at4971598a5b14b62207076dd2da4264c139423628 were
independently compared with the deployed Git-object export. Public npm
CLI0.5.10 and public PyPI client/server0.4.0a7 were used without local wheel
replacement. Build exited0/30.949s, Plan0/1.316s, and ordinary Apply0/372.713s,
recorded2026-11-06T17:30:15.554483Z, with status/phase ready. No manual
Dispatcher driver or receipt rewrite was used. The receipt records three
Server FC roles and one Guest template.

The template's actual afterReady check completed two Qwen Agent turns through
the candidate Gateway, downloaded CSV and source artifacts, verified summary
30.00/10.00 and shares0.750000/0.250000, then Close/Delete. The final controlled
report is status passed/phase complete/code passed with both cleanup booleans
true;17 rows/SHA-256
b1fab8f01af8dc3cff65b73a1a528ca1d1593396e6a37985e8669fb0fb49d1e1.
These are actual assertion summaries. The hook's generated source originals
were not retained as public attachments; historical code/heldout artifacts are
not substituted for them. This does not assert full39 API, SSE, active cancel,
Codex or upgrade coverage on the current recipe. Business HTTP requires only
the Gateway and business key; engineering deployment/inspection uses separate
management credentials.

Normal Destroy exited0/6.374s at17:37:26UTC, with drain confirmed, no retained
revision, and confirmed three functions, one template and Server-image cleanup.
Fresh native checks at17:50:42UTC returned supported typed NotFound for all
three Function names and the exact original-team Template ID; the complete
Sandbox inventory exhausted with zero matches for this run. The hook saved no
native Sandbox ID, so no direct-known-ID check is claimed. Temporary RDS was
independently confirmed deleted by strict native zero inventory at
17:43:12.301UTC,17.992s command duration. Three exact Guest image tags passed
independent absence at17:46:33.732353UTC/54.656s: one was already absent and
two were deleted. Original receipts/journals were preserved.

The final two exact owned empty repositories also passed one-shot Delete and
independent native typed NotFound: Server0/42.149s at18:01:36.308392UTC,
Guest0/39.724s at18:02:31.672104UTC. Both original four-row journals preserve
intent, ACK and typed-native-repository-absence confirmedtrue. SHA-256:
Server b6e18e648217be4ac041d50aa247d58b07187bd0eefc21567f7bceaa56bdc14c;
Guest3b85ff425e557b519313a95b459c21e4bbe4c1ceab67ab6b6ca9bb8cdbee5d5b.
All currently known owned temporary resources are released; borrowed network,
roles and shared resources were not removed. No account-wide absence or
additional business test is claimed. The current source-head
remote e2e42258520960, L1 images42258520964 and explicit-authorization
canonical42258520972 workflows all completed success. Required current-head
review/CI and normal PR merge remain contribution gates, not new cloud scope.
