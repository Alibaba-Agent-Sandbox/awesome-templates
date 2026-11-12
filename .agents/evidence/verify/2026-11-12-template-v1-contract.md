# Verification: inactive canonical template v1 contract

- Date: 2026-11-12
- Result: PARTIAL — local contract implementation passes; active consumer migration and required real end-to-end acceptance are not complete.
- Base revision: `0c8f3f35b113d1f4cc906c39fc64a846196a78a0`; scoped candidate paths are the new `contracts/template-v1/`, two v1 schemas and this decision/evidence.
- Tracker: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/309
- Environment: Node22.22.2, Python3.13.13, AJV8.18.0 and jsonschema4.26.0. No cloud/model credentials used by these checks.

## Verified behavior

Both languages consume actual shared schemas and produce deep-equal complete resource/default/
private execution meanings. Checks preserve native Worker memory4096, explicit auth and native
RAM-role authority, alternate Python Dockerfile profiles, lookup aliases and environment
intent. They reject wrong stages/unsupported inputs, ambiguous or stale references, generated
property conflicts, missing third-party descriptor validation and nonfinite cross-language
numbers. Intent expressions remain intact; resolved values require a separate validation stage.
Sensitive input is absent from both error messages and rendered Python exception context.

## Commands and results

| Command | Result | Scope |
| --- | --- | --- |
| `npm ci --ignore-scripts --prefix contracts/template-v1` | PASS | Reproducible fixture validator dependencies; no installed modules tracked |
| `npm test --prefix contracts/template-v1` with intended Python environment | PASS | 16 valid,39 invalid resource fixtures and5 invalid Registry fixtures; complete JS/Python result equivalence |
| `python contracts/template-v1/test_contract.py` | PASS | Eight contract/semantic/error-boundary tests |
| `ruff check contracts/template-v1/normalize.py contracts/template-v1/test_contract.py` | PASS | New Python sources only |
| `python scripts/test_spec_tools.py` | PASS | 60 existing tests; intentional child conformance/time-limit negative scenarios are not active-catalog failures |
| `python scripts/check_template.py --all` | PASS | Existing active catalog reports zero claimed spec failures; it is not using new v1 yet |
| `python scripts/check_docs.py` | PASS | Local Markdown link checks; no network/cloud calls |
| Candidate migration validation through actual jsonschema plus normalizers | PASS | All48 candidate resources and47 optional publication descriptors; intent/static semantics only, active manifests unchanged |

The final scoped file identities and exact command exit results are also captured in the
candidate verification manifest under the task artifacts. Inactive source copies have no
invented producer commit: they remain an uncommitted candidate until the normal owner review
and delivery workflow establishes a committed source identity.

## Failures corrected during preparation

An initial generator syntax error was corrected before producing schemas. Focused Python
format/import/style checks were corrected. Validation-error handling was strengthened so
jsonschema instance values cannot leak through Python exception context; a regression checks
rendered tracebacks. These preparation corrections do not represent cloud/runtime observations.

## Not verified

- Actual official Devs expression execution, plan redaction and CLI/SDK consumer integration.
- Native FC full props schemas, plugin/backend preparation or instance acceptance beyond the
  stated source-level input subset; the third-party fixture descriptor is not a real backend.
- Image build, real cloud/model turns, old Session routing, close/delete or independent resource release.
- Full cross-repository activation, publication, package release or merge. No active v1 command
  or deployability claim is made by this contract-only change.

## Cleanup

No cloud resources or model tasks created. Fixture Node installation stays ignored under its
own directory; Python bytecode is ignored. Existing templates, golden/history evidence and
other task changes are preserved.
