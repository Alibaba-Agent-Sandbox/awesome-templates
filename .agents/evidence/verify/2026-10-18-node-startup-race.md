# Verification: Node startup race

Date: 2026-10-18. Result: PARTIAL; scoped local behavior PASS, remote checks pending.
Base: main 5ae1078286eb9a93b6ea703274c8a9433c498997.
Environment: Linux x86_64, Python3.13, Node22.22.2, pytest9.1.1, paired
client/server0.3.0 built from clean SDK421ee4da78a1014e4e925a42edb6d9c4bf00b2b5.

- `python -m pytest -q node-web/test_startup.py`: before fix FAIL (DID NOT RAISE),
  after fix 1 PASS. Uses delayed actual Node, with owned group kill/reap in finally.
- `scripts.run_local_e2e._run_one(node-web, venv_bin)`: real HTTP 9 PASS,0 FAIL,
  0 SKIP. Missing entry returns500; actual uploaded app starts, HTTP operations,
  shell and file roundtrip pass; the suite terminates its owned app/server.
- Static spec/checker outcomes are recorded after execution below.

CI diagnosis: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/39111304363
failed on push; https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/39111307478
passed on pull_request. Both report cc69f1b9; the latter checks out synthetic
merge f5d1e61 while push checks out cc69f1b9. Both SDK checkouts are 3c27c675.
The controlled delayed-Node regression proves the timing defect independently
of the event type. Do not delete or relabel those historical outcomes.

This local check is L0, not Docker image build, template image deployment, or
all-template acceptance. No cloud credentials uploaded to Actions, no manual
cloud workflow dispatched, no provider badge changed. Local Express model and
source-runtime verification lives in the integration owner's separate evidence.
Refs https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/112.

- `python scripts/test_spec_tools.py`:19 PASS (unit fixtures include simulated
  failures; these are not real cloud runs).
- `python scripts/check_template.py --all`:exit0, spec_version2 failures0;
  13 legacy product warnings remain. This is not strict modern-catalog acceptance.
