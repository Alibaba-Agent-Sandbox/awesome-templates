# Current CLI workflows verification

Scope: current template READMEs, current user/reference/contributor guides,
managed documentation, document checker and executable public launch harness.
No ordinary template manifest, runtime source or historical receipt was changed.
The shared defaults implementation was committed separately at
084621bb2d82c25b821d046470fbdc92101bba6f.

- Specification suite: PASS, 58 tests.
- Full template checker: PASS.
- Documentation tests, managed catalog and launch contract: PASS, 40 tests.
- Local documentation links: PASS, 234 documents.
- Managed catalog validation: PASS, zero violations.
- Public harness regressions: PASS, 42 tests before final provider --yes alignment;
  final combined harness/parser result recorded below.
- Existing generated launch/process/controller sources were checked unchanged
  during the shared-contract verification.

The first harness collection lacked httpx; installed httpx 0.28.1 in the isolated
validation environment and reran successfully. Actual parser tests were initially
skipped with no ABX executable, then run against the coordinating CLI source build.

README changes alter source identity under the existing qualification algorithm.
Historical evidence is preserved, and mismatched receipts do not qualify the new
identity. This is not a new all-template cloud acceptance claim. No cloud resources,
model runs, CLI release or production publication were performed by this work.

Final local harness/parser run: PASS, 45 tests and 6 subtests, with ABX pointing
to the coordinating CLI's actual src/bin/abx.ts through its installed tsx executable.
This checks deploy/build/provider-operation help and sandbox exec dispatch without
backend credentials. An earlier run against stale dist failed the newly added
provider template.delete help; current source passes without weakening assertions.
Final documentation link rerun: PASS, 234 documents; git diff --check: PASS.
The CI parser job still needs its fixed CLI source commit before publication;
its previous published 0.5.6 dependency cannot validate the new commands.

The active image/steps preparation and managed-template harnesses were subsequently
migrated from the removed native/template and root runtime commands. Native CRUD
now uses provider run with structured input and the actual template/templates
response envelopes. Existing readiness, owned-ID, lost-response, delete-readback,
image digest and credential storage assertions remain intact. No cloud test ran.
The default CLI source requirement stays Node 20+ as declared by package.engines;
local validation used Node 22.22.2. Managed logs documentation now states that FC
logConfig must be configured and is absent from the default recipe.

The portable Python 3.11 build lacks os.memfd_create, causing the existing anonymous
RAM credential test to fail. Repeating in an isolated system-Python environment
with Linux memfd support and pinned dependencies passed that unchanged assertion.
The first combined run there lacked jsonschema; installed requirements-spec.txt
and reran the affected suite. Final results are recorded below.

Final expanded harness run: PASS, 107 tests and 6 subtests, including actual
compiled CLI parser checks plus public, image and steps lifecycle regressions.
Active scripts compile successfully. Final document check: 234 documents, no
local link failures. These local checks did not perform any cloud mutations.

The manual public-template-launch workflow now defaults to its existing source
mode. The managed job can build the exact reviewed cli_ref with npm ci/build/link
while retaining released Python dependencies. Its result records source versus
published accurately. Workflow YAML parsing passed; no GitHub Actions cloud run
was requested for this migration.

Additional existing managed-verifier/materializer checks: PASS, 21 tests in the
system Python 3.13.5 environment, including all-catalog offline step preparation.
The final native image/steps preflight asserts actual create schema fields before
archive transfer or cloud writes; 32 affected tests and the real compiled CLI
create-help preflight passed. No assertion was relaxed to accept old commands.

Independent review by the CLI implementer confirmed the native payload and response
shapes. Its credential review identified inherited registry-password argv exposure;
the image harness now sends those JSON bytes through an inherited anonymous memfd
and --input-file, without a credential-bearing disk file or command argument.
The combined relevant suite passed 109 tests and 6 subtests. The final archive
suite passed 28 tests including an actual subprocess fd handoff, fd closure and
secret-free argv/log assertions. All tests use synthetic credentials locally.

Final parser CI is pinned to CLI source commit
`2eecb789beda997cd8090dd0244e93695d6615c2`, checked out separately and built
with npm ci/build before executing the existing real parser tests. It no longer
installs the incompatible published 0.5.6 CLI. Current Express/image/steps
maintenance guides now name that source distribution, retain published SDK
dependencies, and describe provider template.create without requiring ordinary
users to split their deploy into manual CRUD. Dated historical evidence remains
unchanged. The final local parser, YAML and document checks are recorded below.

Final check results: actual compiled CLI parser tests 2/2 PASS; current-document
links 234 documents / 0 failures; documentation tests 4/4 PASS; both changed
workflow YAML files parse; git diff --check PASS. These checks did not submit
cloud work or execute GitHub Actions.

CI follow-up: the reviewed CLI reference advances to
`3a93c8192a6ebd74bc23294931ee9e6b90d4ccff` for clean-install type dependencies,
its MCP artifact workflow and corrected current documentation. This changes no
template runtime contract. Repeated actual CLI parser checks passed 2/2 and the
consumer workflow YAML parsed successfully; no cloud verification was repeated.

The final exact CLI pin is `ba52904b4f099ffa50d9017e2a4260dff3c0aeeb`.
Its only additional change after 3a93c819 is a CubeSandbox test invocation fix;
consumer parser behavior and the documentation content are unchanged. Workflow
YAML and diff checks passed again. No template cloud acceptance was repeated.
