# Verification: published CLI0.5.10 deployment prerequisite

- Date: 2026-11-06
- Change: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/295 and https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/296.
- Result: PARTIAL — formal CLI availability and all local checks pass; new0.1.4 hosted qualification remains pending.
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

## Local checks and next gate

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

The new recipe's complete
public Gateway, actual model/source, upgrade/retirement and independent resource
release remain required. No cloud resource is created by these local checks.
