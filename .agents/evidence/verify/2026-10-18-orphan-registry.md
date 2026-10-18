# Verification: orphan registry artifacts

- Date:2026-10-18
- Result:PARTIAL; scoped checks PASS; local runtime prerequisites and hosted CI remain separate.

Earlier eight-owner reachability/source review found no executable consumer of
the HTML/JSON pair beyond its own fetch. The actual registry reads YAML and
provider metadata. This standalone main-target change removes only those two
files and corrects root ownership guidance; no template/YAML/evidence is edited.
The larger integration PR109 independently contains the same retirement.

Scoped evidence: scripts/test_spec_tools.py19 PASS; check_template.py --all
exit0 with legacy warnings for the16 existing products (not modern strict
conformance). Consumer search in eight owners found no executable reference
outside the removed pair; registry/scripts/build_data.py ingests YAML directly.
No YAML/template/runtime/provider evidence bytes changed.
Full local source HTTP run:16 PASS /1 FAIL across16 products+skeleton. OpenCode
fails because installed1.18.33 differs from pinned1.19.0 and its fixed image path
is not writable in this host. This prerequisite failure is unrelated to deleted
HTML/JSON; it remains disclosed, not called PASS. Hosted CI remains pending.

## Current-head convergence after startup repair

The old cc69f1b9 head had both successful PR and failed push runs. Logs and a
controlled delayed-real-Node regression establish a main-branch startup race,
not a consequence of removing catalog assets.
https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/113 merged at
4eb66f7577522fc7036d08dd3e6f4595ee707940 after its current-head basic check passed.
This branch ordinarily merges that accepted main; the SDK input is now immutable
and feature push checks are removed, while PR/main checks remain. Historical
failed results are retained. Current-head required checks must pass before merge.
The separate 23-template source-runtime/model and image-deploy gates remain separate.
