# Verification: managed runtime catalog

Result: PARTIAL (runtime checks PASS; latest-head CI/merge pending).

Real native SDK0.3 from d4d93e8cbb986f33a8868f7a4139ed0edb49eaba and CLI0.3.0. Both provider-managed IDs passed actual SDK shell inventory, file roundtrip/removal/absence, run_code result42 and real CLI exec42. Each owned sandbox was killed and independently absent from paginated SDK inventory. No template definition was modified or deleted.

Base observed Python3.13.13/Node20.20.2/Git2.47.3, without numpy/pandas/matplotlib/ipykernel. code-interpreter-v1 additionally observed numpy2.4.6/pandas3.0.3/matplotlib3.11.1/ipykernel7.3.0. Both native interpreter RPCs returned404 and SDK shell fallback handled execution. Native interpreter/context features remain unverified. Receipts are under docs/managed/evidence; observed versions do not pin mutable provider images.

Specific catalog-only scope from Issues31/32 is implemented; copied source Dockerfile/deploy/named-command criteria do not describe these managed definitions and were not run. Source catalog selectors remain unchanged. Credentials, raw logs and sandbox IDs remain outside public records.

Executed static checks: Markdown links118 documents/0 failures; strict source
conformance23 plus skeleton/0 failures; test_spec_tools37 tests PASS. Native
CLI help was checked for create --template/timeout, exec and cleanup syntax.

CI selector follow-up: preserve the frozen23-template canonical source approval
boundary while permitting new independently verified catalog entries. The
authorization regression rejects every unreviewed added name; no credentials
or cloud workflow authorization are broadened.13 real authorization tests PASS.
