# OpenSandbox controller and documented business follow-up

Result: PARTIAL (scoped proxy correction passed; catalog-wide work remains open)

Date: 2026-10-27. Runtime templates: public source50d7e38cd5837042acb756aad66d8f97050f11dd
or a63f0f8f8996fd772116c570aa21e927dcc1aea0, as recorded per receipt. Template
runtime and per-template HTTP controller bytes were unchanged by this patch.
Public standalone CLI0.5.7, Python client/server0.4.0a6, Docker29.9.2/classic
overlay2/MTU1450. Owned loopback OpenSandbox1.1.1, fixed execd
sha256:cda2bc35409bbf57561599b316cafb899598f7dce671332e7ceda14eb1cfeded,
owned disposable local image registry. Existing unrelated listeners were left
alone. No GitHub secrets or management API keys were created/restored.

## Preserved real failures and correction

- [Attempt1](2026-10-27-business-cases/python-hello-proxy-failure-01.json): FAIL,
  controller1 pass/12 failures because Bearer did not survive the proxy. The
  cleanup helper also failed to recognize the published generic E2009 error.
- [Attempt2](2026-10-27-business-cases/python-hello-proxy-failure-02.json): FAIL,
  17 pass/4 failures, all bodyless application DELETE400. Authentication and
  named commands worked; sandbox/template/image deletion was confirmed.
- [Attempt3](2026-10-27-business-cases/python-hello-proxy-pass-03.json): PASS,
  all21 controller assertions plus eight literal CLI/SDK/HTTP/fresh-file checks,
  zero fail/skip/not-run. Actual downloaded summary.txt equals total=51.30 plus
  newline. Previous outputs were independently absent before the next consumer.
  The unchanged default Docker recipe was built and used, not only published.
- [Independent reconciliation](2026-10-27-business-cases/opensandbox-owned-absence-reconciliation.json):
  every owned sandbox from all three journals returned lifecycle404 and had no
  matching Docker container. No resources were created for reconciliation.
  This records actual absence despite the original typed-exception mismatch.
- Adapter SHA used for successful actual proxy run:
  f3f71110b6f623042d8f3b1b280cd0cd704f43b94291364ca60bb2e9691be80a.
  The later unchanged-input guard is unit-verified and does not change requests.

## Other actual business cases

- [OpenCode core](2026-10-27-business-cases/opencode-core-express.json) and
  [fresh documentation](2026-10-27-business-cases/opencode-docs-express.json):
  actual repair/preserved original tests/held-out assertions/session continuation,
  all six methods, literal CLI/complete SDK/HTTP, independently executed downloaded
  Python, and real second-model generated/downloaded artifact. Old output was
  absent before SDK and HTTP. Both source snapshots match by immutable staged
  source digest; the core's abbreviated requested commit is resolved explicitly.
- [Aider core](2026-10-27-business-cases/aider-core-express.json):21 assertions,
  real default read-only ask, explicit writeback, changed source/report, preserved
  tests and independent original/held-out checks. [Literal use](2026-10-27-business-cases/aider-docs-express.json):
  eight fresh-output assertions via CLI, complete SDK and HTTP, using a second
  startup model qwen3.8-max after core qwen3.8-flash. Downloaded generated Python
  independently prints Hello from the sandbox. Actual command output confirms
  selected generated_hello.py and GENERATED_REPORT.md writeback.
- [apply-patch core](2026-10-27-business-cases/apply-patch-core-express.json):
  actual native version, add/update/move/delete/literal text and failure/path
  controls. [Literal use](2026-10-27-business-cases/apply-patch-docs-express.json):
  eight fresh CLI/SDK/HTTP assertions; independently downloaded hello.txt is
  exactly Hello from a patch plus newline. All three named methods exercised.
- [Managed base](2026-10-27-business-cases/base-express.json): literal CLI and
  complete SDK creation/process/file use; actual CSV/Decimal task produces
  independently downloaded {count:3,total:"51.30"}; process exit7 preserved.
  All task files and both created instances independently absent. Runtime Python
  3.13.13. No image preparation, model or project HTTP server was claimed.
  [Complete article program](2026-10-27-business-cases/base-article-express.json)
  separately ran unchanged, with exact output and its owned instance absent.

Every listed completed case confirmed its owned sandboxes/prepared artifacts
absent, zero retained/uncertain outcomes. Private IDs, endpoint/key values and raw
model/SDK logs are excluded. Sanitized copies identify the original private
receipt hash; a referencing core hash may therefore identify that original,
not the sanitized copy's bytes. These are operator-run records, not CI attestations.

## Local checks and remaining gates

Targeted controller/launch tests: PASS,75 tests and two subtests.
Document links: PASS,224 documents/zero local link failures before final record.
Actual OpenSandbox and Express receipts above establish their stated inputs and
business scope. Full remaining-template/missing-account/model/public-method and
per-template article completion remains under244 and blogs16. OpenCode's separate
OpenSandbox model run and the compatible-model core matrix are still running;
no uncompleted run is counted here. Registry reviewed receipts and source-owner
CI/merge/publication remain separate gates.
