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
