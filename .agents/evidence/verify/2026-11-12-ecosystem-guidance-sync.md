# Verification: ecosystem guidance synchronization

Date: 2026-11-12
Result: PARTIAL
Baseline: a34a709bc79ef0e1442cb43efe2d4bb49c2ee190

## Scope and review

Audit all catalog entries and source/managed documentation. Correct root discovery, issue reproduction, skeleton and recipe comments, current controller documentation and Amp/Codex controller instructions. Dated acceptance evidence remains unchanged; no runtime qualification is inferred from prose or comment updates.

Command spellings and options were compared with the current parser and built help. Replacing historical result text, adding aliases, modifying runtime algorithms, upgrading template dependencies and recreating cloud resources were excluded after examining whether they were necessary for this task.

## Results

Local checks are recorded below. No cloud resources were created. Existing runtime receipts were preserved; modified source identity does not inherit a new qualification.

## Delivery limitations

The root dotenv's configured GitHub credential returned HTTP401, no alternate process credential or configured Git credential helper/gh session was available, and private Registry/Website fetches could not authenticate. Public producer main revisions were fetched and checked. Private consumers are based on the latest locally recovered task branches, not claimed current remote main. Finish local commits and reproducible bundles; push, PR, remote CI, review and merge remain blocked until authentication is restored. No new package, image or live website release is claimed.

## Local verification

- Current Markdown checker: 234 documents, zero failures.
- test_spec_tools.py: 59 tests passed.
- check_template.py --all: zero non-conformant entries and zero claimed spec failures.
- Lychee 0.24.2 offline with fragments: all 636 tracked Markdown inputs pass.
- Initial catalog/spec checks failed because the fresh validation venv lacked the pinned jsonschema dependency. Installing scripts/requirements-spec.txt resolved the prerequisite; the unchanged assertions then passed.
- Template README/runtime/manifest content was inspected across the complete catalog. The first literal scan covered retired root commands but missed the unsupported sandbox run spelling. Comparing actual built parser help exposed that this spelling was still required by the checker and used in the READMEs and controllers. The final verification below supersedes that incomplete scan.
- Five Dockerfile edits change comments only, including the skeleton. No Docker instruction, dependency, model/business function, manifest or acceptance receipt was modified. Source identities can still change under the existing conservative hash rules; no new qualification or image/cloud test is claimed.

## Supported named-command correction

The current parser supports `sandbox command run`, not `sandbox run`. Updated
all affected source template READMEs, the skeleton, public usage/spec pages and
both active public-launch/image-verification controllers. The checker now
requires the supported entry; a new bilingual regression failed both cases
before the fix and passed after it. The CLI-only instructions no longer require
manually generating an application token: they explain the generated/saved
default and the optional custom value for external SDK/HTTP consumers.

- Full spec regression after the fix: 60 passed.
- Full catalog check: zero non-conformant templates and zero claimed spec failures.
- Current local document checker: 234 pages, zero failures.
- Current Markdown links/fragments pass after the final edit.
- Actual compiled CLI parser and controller tests are recorded below.

These changes do not alter business code, Docker instructions or runtime API
implementations. All historical receipts remain tied to their original source
identity; no replacement qualification is claimed.

- Real compiled CLI parser contract script: 2 passed, no credentials or cloud calls.
- Public-launch and image-archive controller selection: 74 tests plus 6 subtests passed. The compatibility fixture now verifies the complete supported command path and retains fresh-script/output/cleanup assertions.

The final global-selector/retired-authoring scan also corrected current image-acceptance docs from the removed from-image command to the existing provider template.create operation.

## Authentication and delivery follow-up

The initial API Bearer request returned HTTP401, but the credential was not
invalid. Git push/fetch and the API's Basic authentication succeeded with the
same existing credential; no credential was changed or created. Public
producer source branches can now be pushed. Private Registry/Website main was
fetched successfully, and the prior coordinating PRs were confirmed merged.
This supersedes the initial delivery-authentication limitation above.

## Serving setup follow-up

The current built CLI at 4367143 acquired `agents-api` through the public catalog
with `abx template init ./agents-api --from agents-api`. It copied the spec6
manifest, server recipe, scripts and exercise files without deployment. In the
resulting project a fresh Python3 venv installed exact httpx0.28.1; the actual
smoke script help ran and copied binding references had mode0600. No separate
mkdir was needed. `abx --json deploy . --name agents-api --bindings
.abx/bindings.json --plan` returned kind=application, profile=fc-managed-agents,
status=preview and builds_or_cloud_changes=false. Config paths were isolated
through the CLI's existing configuration seam; source fetching/parser/filesystem
were actual components, not mocks. No cloud or model request was executed.

The updated managed-document fixture first failed on the old SDK-title
requirement (one of13 tests failed). After the checker/spec were aligned with
the truthful Python HTTP-client heading, all60 spec tests and the complete
catalog check passed (zero nonconformant entries). The managed fixture also
rejects missing httpx in both languages. Full documentation checking passes;
one initial invocation failed due Git safe-directory configuration, then the
unchanged checker passed with explicit worktree ownership configuration.
Source identity/acceptance and the existing LibreOffice gate remain unchanged.
