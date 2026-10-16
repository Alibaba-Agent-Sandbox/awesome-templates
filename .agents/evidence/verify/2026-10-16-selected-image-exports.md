# Selected image CI and export preparation

Date: 2026-10-16
Result: PARTIAL

## Scope

Independent Pi branch based on 7cb0d9430768eec22f500ebb80b3fe9517ab1cbc. Changes are image workflow dispatch/plan/generalized archive, `scripts/select_image_templates.py`, its regressions and the existing context regression's catalog-driven coverage. Existing PR 82/running 16-image workflow was not modified or retriggered.

## Safety review correction

Initial PR synchronize planning used the last head. Independent review found that runtime A failing image checks followed by docs-only B could then produce an empty current gate. That approach was removed before commit. PRs now compare cumulative base to head. Main always builds all catalog products; no prior successful input-hash proof is assumed. A runtime-changing PR's later prose commits can repeat image work; that efficiency limitation remains explicit.

## Verification

- Final scoped pytest: 68 distinct tests PASS (Pi 45; image selection 23). Regression source/helper files conservatively select their owning image too.
- `python scripts/test_spec_tools.py`: 22 PASS, including all 17 real template contexts.
- `python scripts/check_template.py --all --strict`: 18 conformant directories, zero failures.
- Both workflow YAML files parsed; every run block passed `bash -n`; all three embedded image-workflow Python blocks parsed. Manual selector executions for Pi and python-hello returned exactly the requested entry.
- `git diff --check`: PASS.

 Required behavior includes a real temporary Git history (runtime A, prose B) whose cumulative selection still includes A's image; strict dispatch whitelist, runtime ownership, main full selection, shared workflow full selection, and prose-only PR exclusion. Actual image contexts are executed through the real preparation block; opaque wheel fixture copying is not installation or Docker acceptance.

No local Docker tests, registry pushes, remote workflow triggers or cloud/model secrets are added by these checks. New 17-product workflow execution and generalized remote archive upload remain NOT RUN until this independent branch is published. The previously observed 16/16 L1 pass belongs to PR 82's 7cb revision, not this new Pi image or workflow.

Independent peer review of the final runtime/verifier/selector/workflow found no blocking issue. The reviewer confirmed owned cleanup, independent target verification, cumulative PR selection and archive provenance boundaries. Output remains buffered in memory without a byte cap; the execution deadline is enforced and this limit is documented.


## Scoped publication follow-up

Draft [PR 86](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/86) initially published b2857609735c1da8529ba8ecf3d065076cdfb542. Review then found stale current Pi text in docs/backlog.md and that manual dispatch availability was not yet verified while the workflow remains outside the default branch. The follow-up corrects the current Pi section and automatically exports only Pi and python-hello from successful automatic jobs, with a regression constraining that scope. Historical survey files remain unchanged. Old-head runs 38851706883, 38851706717 and 38851684272 were requested cancelled before the scoped source follow-up; cancellation is not a passed check. New-head image/archives remain pending actual CI.

Follow-up verification: selector/archive-policy pytest 24 PASS (one added case; 69 distinct cases combined with unchanged Pi suites), spec tools 22 PASS, all 18 directories strict conformant, workflow YAML/shell/embedded Python syntax PASS and git diff check PASS. This is preparation only; no new image result is claimed.
