# Image CI and acceptance checkpoint

Date: 2026-10-16
Result: PARTIAL

## Scope and provenance

Documentation-only branch based on Pi source
`a361f490555ead0ff67081ffb4874abf292a1b2f`. Changes are the bilingual
`docs/verification-2026-10-16.md`, this record, its process note, the public
[machine-readable run snapshot](2026-10-16-image-ci-checkpoint.json) and the owner
record index. No runtime, Dockerfile, workflow, catalog, template evidence or
provider metadata is changed.

## Actual remote image results

GitHub's run and jobs APIs were read independently during this checkpoint. Both
reported `status=completed`, `conclusion=success`, the expected exact head and no
failed/skipped image job:

- `7cb0d9430768eec22f500ebb80b3fe9517ab1cbc`:
  [run 38850050144](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/38850050144),
  16/16 actual image jobs successful.
- `a361f490555ead0ff67081ffb4874abf292a1b2f`:
  [run 38853293050](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/38853293050),
  17/17 actual image jobs and the plan job successful. The reviewed artifact
  inventory contains 17 exported images for this same run/head.

These are L1 results. The initial 13/3 outcome remains unchanged in
[first-CI evidence](2026-10-16-image-build-first-ci.md). Earlier Pi source/model
and offline-tool records also remain unchanged; the former's 17-check real
compatible-model pass belongs to `b2857609735c1da8529ba8ecf3d065076cdfb542`.

## Supplementary cloud failure retained

The integrator's production-Builder Python hello image attempt actually pushed
the image, reached official template READY and passed hello/run_script through
SDK, CLI and HTTP (six calls). Its full HTTP suite then reported zero PASS,
one FAIL and exit 2 on preflight `/health`. The controller omitted required
network proxy configuration. The sanitized report records successful cleanup of
the owned sandbox, template, registry tag and repository. Overall result remains
FAIL; a corrected controller or pending new attempt is not acceptance.

This checkpoint observes that report; it did not create a cloud resource or
repeat the attempt. No private endpoint, template ID, registry name, credentials,
signed URL or raw model/provider log is copied into this repository.

## Canonical acceptance interpretation

The specification's Test levels table requires `abx template deploy` READY.
CONTRIBUTING checklist 7 and specification Contribution 7 additionally permit
committing `evidence/express-<date>.json` only after
`python3 scripts/express_e2e.py <dir>` exits 0. Therefore CI image transfer plus
official registration and external smoke can be recorded as supplementary
changed-image cloud verification, but cannot silently replace that L2 gate or
populate provider-pass evidence, `tested_on` or README Verified.

Pi cloud/image-backed L3, Aider PR 88 development, the OSWorld issue 36 slice and
the remaining original business roadmap are still open at this checkpoint.

## Local validation

- PASS: `python scripts/check_template.py --all --strict`, 18 conformant
  directories, zero failures.
- PASS: all 17 relative Markdown targets in the four scoped documents/index
  resolve to real files; the machine-readable snapshot parses and its image
  counts are 16 and 17.
- PASS: `git diff --check` and scoped diff review.

Remote draft-head CI has not yet run. No local cloud/model test was required or
claimed for this documentation-only change. The draft is intentionally unmerged.
