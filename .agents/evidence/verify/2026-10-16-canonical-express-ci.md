# Canonical Express CI preparation

Date: 2026-10-16
Result: PARTIAL

## Exact scope and source

Separate workflow/controller/test/bilingual guide and owner records, stacked on
cleanup fix 3572927fbd0ab25ad028a9186bc2820ff7a8a854. Existing template runtime,
Dockerfiles, L1 workflow and provider-pass records are unchanged. The new workflow
pins immutable a361f49 template inputs, cleanup-fixed 3572927 canonical runner,
production CLI 37b6d27, accepted controller SDK 666657b and e2cb27e server source.
Those are separate checkouts; an old workspace dependency definition is not
modified to make it installable.

## Gates and tested behavior

- PASS: 12 standard-library unittest methods exercise exact opt-in/head/fork
  authorization, strict one/small/all-17 selection, missing credentials before
  any source/cloud call, refusal of a failed canonical exit despite a receipt,
  failed compute cleanup preserving registry, failed registry cleanup refusing a
  receipt, and publication after all fixture gates succeed.
- Initial positive receipt test failed on a missing artifact output directory;
  the controller now creates that owned directory before copying. The corrected
  12-method run passes (2.404s). This was local fixture/controller verification only.
- Actual CLI flag contracts and official ACR ROA GetRepo/DeleteImage/DeleteRepo
  paths were read from the existing reviewed CLI/harness and official generated
  Alibaba SDK source. No endpoint or wrapper command was invented.
- PASS: real local Linux success 0/nonzero 7/timeout leaders leave no owned
  redirected descendant. WNOWAIT holds the leader until group kill and reap.
  The controller also forwards Requests/curl CA bundle settings and excludes
  unrelated model keys. Fixture receipts crossing UTC midnight are accepted;
  private-value receipts are refused.
- PASS: final YAML/source-pin/Python syntax, strict checker (18 directories),
  scoped relative links and diff checks. Configured-secret scan covers staged scope.

## Unrun, blocked and ownership limits

No cloud key was uploaded, no Actions secret/environment was created and no cloud
run was dispatched. No Docker build, registry push, official cloud mutation or
model request was executed by this preparation. Twelve unit methods are not L2.
Missing approval/configuration yields explicit BLOCKED status. A green plan check
only validates preparation and is not a provider pass.

Canonical evidence requires runner exit 0 plus validated fresh pass JSON and
cleanup, including canonical independent official alias/SDK sandbox absence
readback; failed/unknown compute preserves registry. Exact ACR tag and repository
delete must read back HTTP 404. An always step retries only private owned intent.
The job and controller have time limits, but forced cancellation/runner loss may
prevent cleanup or lose the VM-local journal; that remains failed/blocked and
requires operator reconciliation by the exact documented run-derived alias.
No cancellation guarantee or broad janitor is claimed. The matrix is serial and
fail-fast to avoid creating more resources after failure.

Temporary test roots were removed. No raw diagnostics, credentials, private
endpoints, resource IDs or signed artifact URLs are included in these records.
The operator must review the concrete workflow and approve the new temporary
credential storage site before the final upload/execution step.

The first workflow push local-e2e run failed before this change's tests while
installing pinned upstream Hermes: curl HTTP 429 (run 38859149702). This external
installation failure is preserved and is not a cleanup/controller regression.
The initial authorization run 38859154201 succeeded and canonical cloud job
was SKIPPED because default authorization remains BLOCKED. Neither is L2 PASS.
