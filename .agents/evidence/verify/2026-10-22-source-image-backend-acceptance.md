# Source image backend acceptance — 2026-10-22

Result: PASS — all three current-source backend qualification columns; final publication gates are recorded below.

Base: da1da4193bb31c28cb252d745b2012fd1d011c4b. Scope: shared HTTP fixture
enforcement, existing Express image runner, optional native OpenSandbox workflow
and controller. No template runtime source has changed at this stage.

- `python -m pytest -q scripts/test_template_http_acceptance.py scripts/test_ci_image.py`:
  PASS36; actual subprocess tests reject false success after required operation
  skips, zero checks or failed assertions and verify operator-key isolation.
- A manual29-template missing-current-image-HTTP export was accepted by GitHub:
  [run39747846635](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/39747846635).
  Acceptance is not yet claimed; the full export/runtime batch is pending.
- Native OpenSandbox pilot/full46 and additional Express image runtimes: NOT_RUN
  at this checkpoint. Full completion and Issue185 closure remain blocked until
  actual per-template receipts pass; existing steps46/46 remain separate.
- No new cloud resource or private registry transfer has been created by these
  local regression checks. Generated test keys are not published. Historical
  merged evidence remains unchanged.

- `python scripts/test_spec_tools.py`: PASS57.
- `python scripts/check_template.py --all --strict`: PASS46 sources plus skeleton, zero claimed spec failures.
- Workflow YAML and both new controllers compile: PASS. New bilingual documentation/record link checks are run before publication.

## First original OpenSandbox pilot

Actual native run39749792427 failed on both python-hello and node-web at the
explicit-user UID probe; SDK/container/process cleanup passed for both.
The unchanged images already select USER user. The next pilot tests the actual
image-default identity and still requires a numeric UID greater than zero;
explicit same-user switching on the legacy execd is not qualified. Preserve
manifest environment defaults instead of replacing published non-secret
settings with empty values. See the dated initial-pilot-failures JSON.

## Second original OpenSandbox pilot

Run39750661983 observed UID1000 and complete actual native HTTP checks21
(python-hello) and60 (node-web); SDK/container/engine/server cleanup passed.
The overall run correctly remains FAIL because the controller queried unused
`opensandbox` client metadata; this fixture installs the original
`opensandbox-server` distribution. Fix the distribution lookup, retain both
failed receipts and rerun the native matrix. No runtime success is published
as an overall pass from this failed workflow.

Shared fixture/image/steps-controller regressions: PASS45.

## Express transfer and command-surface regressions

All29 missing-current-image-HTTP source images exported successfully in
run39747846635. First two transfers failed before native runtime: the task driver
had relocated all temporary directories to the object-backed workspace, which
cannot create the registry-auth fd symlink (actual errno22). Add an explicit
private archive root without moving RAM-only auth away from the native temporary
filesystem. Keep actual auth bytes in anonymous RAM. Deleted2,110,424,490bytes of
resolved first-transfer archives; retain small failure/ownership records.

The next two attempts uploaded verified private images but the existing harness
called removed `template create`. Actual published CLI0.4.1 and sourceCLI0.4.5
both expose `template from-image`. Both requests were rejected by the parser
before a registration callback; no known template/sandbox IDs and no sandbox
create attempt. Independent official exact-alias and SDK absence checks passed;
registry cleanup also passed. The original attempts remain FAIL. Correct the
canonical image route and receipt operation; preflight the actual CLI help before
archive/cloud operations. The existing image lifecycle regression failed before
that correction. A new local-protocol-helper regression also failed before adding
transitive dependency preflight.

Verified publisher assets independently match the actual local tools:
CLI0.4.1 SHA256766b0b10c3e4c633632dad503ae7750183a8be41974a9d048f060836f8cb0c44;
crane0.22.1 SHA2568e75c326adb43b053cfd78b9b987663f8f4fe4557f4d3915905643f25c730992.
Express controller SDK source:34e7e011c5569f77b7f605e65313be7498f6cf02.

## Native source matrix and Chrome controller dependency failure

Native run39751400293 produced real individual source API/HTTP and independent
cleanup passes; its full matrix is still in progress. Chrome's real native image
and shell/named smoke passed, but external HTTP failed8PASS/1FAIL because the
controller's local CDP/RFB helpers need aiohttp and Crypto. Keep this as FAIL and
add the existing complete hash-locked chrome/requirements.lock to the native
controller environment. The local transitive-helper preflight failed before
correction and passes afterward; no template source or native runtime gate was
weakened. Native cleanup passed for the failed Chrome attempt.

## Transport and conditional dependency corrections

Actual Express image registration, SDK creation and CLI/native SDK smoke now
work through public `template from-image`. The full HTTP child lost the
operator-configured SSL_CERT_FILE, causing real certificate verification errors.
Preserve only non-secret SSL_CERT_FILE/SSL_CERT_DIR alongside the existing
controller allowlist; never disable certificate verification. A real TLS/HTTP
subprocess fixture using a Unix socket passes after correction. The TCP fixture
was affected by transparent loopback TLS interception; explicit Content-Length
avoids TLS EOF ambiguity in the Unix-socket fixture. Public external HTTPS
verification with the configured CA also passed without an API credential.

Chrome rerun39756780475 stopped before native runtime installation: strict hash
mode needs Python3.12's conditional typing-extensions dependency, absent from
the browser lock generated for Python3.13. Add a supplemental lock for the paired SDK-compatible conditional dependency,
using publisher release hashes.
Keep strict hash verification and uv pip check; no dependency gate was bypassed.

The initial supplemental upstream-server typing4.15.0 pin conflicts with the
paired SDK's Pydantic2.14/anyio dependencies requiring>=4.16.0. Local dependency
validation caught it; cancelled the superseded native dispatch before backend
creation. The corrected4.16.0 pin and both file hashes come from the publisher's
PyPI release metadata. Hash-enforced install and pip check now PASS. Targeted
controller/image/qualification/steps regressions PASS69; verified HTTPS includes
a real self-signed TLS/HTTP fixture over Unix socket and an external transport
preflight, with certificate verification enabled throughout.

## API completion and additional provider publication gate

Original native run39751400293 supplied45 passing source SDK/full-HTTP receipts;
Chrome rerun39761201042 supplied its30 passing HTTP checks and independent
cleanup. These46 API/HTTP results are preserved as historical evidence. They do
not yet qualify `tested_on`: the template specification also requires genuine
CLI and SDK command records. Add actual pinned-provider CLI `exec` into the
owned guest to call every manifest named HTTP smoke, independently repeat
through ServerClient, and rerun the native matrix with both command records.
Do not substitute a generic `abx run` capability or weaken the specification.

The portable Express batch now uses at most four isolated worker processes,
skips current qualified inputs, and stops new operations after uncertain cleanup.
Its regressions and current qualification/controller/prerequisite checks passed:
`pytest -q scripts/test_source_image_acceptance.py scripts/test_template_http_acceptance.py scripts/test_image_e2e_batch.py scripts/test_ci_image_archive.py`: PASS46.
The prerequisite ordering also preserves the existing missing-controller-module
diagnostic before CLI availability checks. Actual image receipts remain separate
from native OpenSandbox source acceptance and model account acceptance.

## Scoped review checkpoint

Reviewed the source/digest and current-controller guards, native CLI operation,
credential isolation, failure classification and owned cleanup paths. Only
`tested_on` qualification metadata is excluded from the manifest runtime contract;
changed runtime/controller inputs invalidate qualification. Native CLI evidence
uses real `exec` into the owned guest named API and never asserts generic native
interpreter or `template launch` support. Both provider controllers require
independent absence readback; Express also requires the owned private-registry
delete/readback. Uncertain cleanup stops new batch operations. Only sanitized
receipts are exported; raw consoles and ownership journals remain private.

Local targeted groups passed46 +177 tests, plus18 subtests. Current source-head
fef1c788103da5b8509cfa5fce71d40ce4109e6b's [five e2e jobs](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/39766701264)
all passed: documentation, local-e2e, native database, document conversion and
media checks. The final publication head still requires its own required CI and
review after the current-source backend matrix and bilingual metadata finish.

Periodic cleanup removed147,205,474bytes of this task's unused duplicate tool
cache. Active image archives, public evidence and private recovery journals were
preserved. Successfully qualified Express attempts remove their own large stages.

## Complete native CLI, SDK and HTTP matrix

[Original OpenSandbox run39766754883](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/39766754883)
finished SUCCESS with all46 individual source images passing genuine CLI and SDK
manifest smoke, unchanged complete HTTP controllers and independent SDK/Docker/
engine/server cleanup. Public date-conforming `opensandbox-2026-10-22T*.json`
receipts are stored in each template's evidence directory. Full sanitized Actions
receipt artifacts were downloaded because GitHub truncates long check annotations;
artifact digests are checked when supplied. Prior SDK/HTTP-only receipts remain
historical checkpoints and do not substitute for the new required CLI evidence.

Native runtime acceptance is complete. Express's final two selected source images
are still in progress at this checkpoint. PR188 meanwhile merged independent
explicit-schema rules; integrate that main revision after the active image workers
finish and use the updated checker without its retired `--strict` flag.

## Final backend result and current-main integration

All46 current sources now pass Express regular-image runtime/independent cleanup,
complete image HTTP, and original OpenSandbox source-image CLI/SDK/full HTTP with
independent cleanup. The final Stagehand and Tau2 Express attempts passed; the
bounded selected batch finished25/25 with no unresolved owned cleanup. Existing
qualified current-source image runs remain valid; this is not a claim of46new
Express registrations. Credential-dependent model/vendor checks retain explicit
SKIP/NOT_RUN and are not promoted to model acceptance.

Integrated current main a6df7ff65a4761e64aacb74b17a5740bdca4204b (PR188/189) after
all live workers finished. Resolved index/CI/test conflicts while preserving
explicit-schema validation, the default template-list route, the actual
`template from-image` registration fix and every new regression suite. Actual
read-only nativeCLI0.4.1 calls to template list with and without the old flag both
returned success and the required Alias/TemplateID shape; no resources created.
Updated bilingual stale checker prose and clarified that sanitized failed-attempt
records never qualify a provider. Runtime image inputs and the native controller
remain unchanged; no backend pass is inferred from this documentation integration.

## Final local publication checks

- `python scripts/test_spec_tools.py`: PASS57.
- `python scripts/check_template.py --all`: PASS46 sources plus skeleton, zero violations.
- `python scripts/check_docs.py`: PASS218 current documents, zero broken local links.
- Explicit task decision/evidence link check: PASS2 documents, zero failures.
- `python scripts/source_image_acceptance.py`: PASS46/46 Express image runtime,
  46/46 complete image HTTP and46/46 original native OpenSandbox.
- `python scripts/step_acceptance.py --require-http`: PASS46/46 current step
  runtime and46/46 complete step HTTP after the qualification-only metadata update.

Permanent [image/backend matrix](2026-10-22-source-image-backend-matrix.json) and
[step recheck](2026-10-22-current-steps-after-backend-qualification.json) retain
individual template/version and receipt paths. [PR186](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/186)
tracks the final-head CI, review and actual merge; no pending CI is called a pass
in these pre-publication records. No template runtime source changed.

After integrating current main and resolving the actual contract conflicts, the
complete affected shared regression group passed223 tests and18 subtests in
183.11seconds. This includes preparation, image/archive/cleanup/SDK creation,
step provenance/assets, required HTTP fixtures, source qualification and bounded
batch behavior. No remaining local gate failed or was bypassed.
