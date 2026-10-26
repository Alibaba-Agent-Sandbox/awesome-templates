# Published template acceptance — 2026-10-25–26 UTC

Status: PARTIAL. Completed test scopes and original failures are preserved below. Default Express Docker remains BLOCKED; this records PR still needs latest-head CI, review and merge.

## Inputs and receipts

| Group | Actual identity and scope |
|---|---|
| Default public Git-source and managed checks | Source/verifier `4229b6c4d96675a05bd0bef031fb36d43f138d14`; published CLI 0.5.6 and Python client/server 0.4.0a6 |
| Frozen native source preparation | Verifier `a9362a8ca988aaed33cd0b19e3ed8ecb4cd88af7`; the same published versions; original direct transport |
| Focused controls | Muse OSS: `a936`; repaired next-app: `3db65881372352f8cc390d54e3550b2d4ea8b6f4`; one post-merge agents check: `c8bc3b19576fe92fee248a380346f51cba94236f` |

The records base is merged main `01279335dd4ecd8b252413344c67a42e59935e4f` ([PR233](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/233)). Merging it does not relabel any prior test source. The [canonical JSON](2026-10-25-public056-template-acceptance.json) indexes 100 original receipts with their path and SHA256. The fixed next-app receipt already owned by PR233 is linked, not duplicated. An additional diagnostic absence receipt is separate from acceptance counts.

CLI release source is `1ea3eabd679c3cf26c824492a60fe2a8aea43f62`; the provider input is `188b04ce98c6b71da0ba4145845fbd925051b03a`. The SDK `source_ref` value `676ef0483706a2b1af717db8d6d08f19acd8d804` in default receipts identifies the workflow fixture checkout, not an independent claim about wheel source. Actual installed package versions and guest readback are separate fields.

## Default documented paths: 50 catalog entries × 2 platforms

| Path | Result | Scope |
|---|---|---|
| OpenSandbox: 46 source recipes | 46 PASS | 219 successful CLI/Python/host HTTP manifest calls; controllers: 628 PASS / 0 FAIL / 18 SKIP; wrong-token and CLI/file checks for all 46 |
| Express: 46 source recipes | 46 BLOCKED | Default Docker-to-ACR preparation could not run with this operator's missing Docker prerequisite; uploading the proposed Actions credentials is not authorized. This is not a template API failure or unsupported-provider claim. |
| Applicable managed entries | 3 PASS | Express base/code-interpreter-v1 and OpenSandbox's native interpreter entry |
| Foreign-provider managed identities | 5 NOT_APPLICABLE | Explicit provider-mismatch rejection, with no replacement image |

Total: 49 default PASS / 46 BLOCKED / 5 NOT_APPLICABLE. The [OpenSandbox source run](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/40239893681) independently confirms all 46 sandboxes and all 46 prepared artifacts absent, with zero uncertain cleanup.

The [OpenSandbox managed run](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/40242123498) includes 17 original interpreter checks: persistent contexts, isolation, exceptions and context deletion. SDK NotFound and Docker absence confirm cleanup. This is the upstream interpreter path, not unified `ProviderSandbox.run_code` support. Express managed data processing uses real numpy/pandas/matplotlib; both Express receipts retain `native_interpreter_verified=false`. Numerical shell execution does not certify persistent interpretation. The E2B-owned desktop entry remains foreign to both selected platforms.

## Frozen native supplemental batch

All 46 original direct attempts completed: 44 PASS / 2 FAIL. Successful named calls total 207. Controllers that ran report 611 PASS / 0 FAIL / 18 SKIP. All 46 prepared templates and all 45 actual runtime sandboxes were independently absent, with zero unresolved cleanup. Guest a6 was read back for the 44 passing cases; neither failure has a guest version readback. A zero controller-failure total does not erase pre-controller failures.

- [Muse direct failure](../../../muse/evidence/verification-steps-2026-10-25T235301Z.json): native registration readiness failed before a sandbox ran. Root cause remains UNKNOWN; the recorded install error and errno do not establish an IPv6 or upstream-network diagnosis. The prepared template was independently absent.
- [Next-app original failure](../../../next-app/evidence/verification-steps-2026-10-25T235550Z.json): the first named command failed on package-file permissions. Its sandbox and template were independently absent. The original result remains FAIL after the later correction.

## Focused controls, counted separately

| Receipt | Result and limits |
|---|---|
| [Muse direct control](../../../muse/evidence/verification-steps-2026-10-25T225635Z.json) | FAIL before application runtime; exact prepared-template absence, no unresolved cleanup |
| [Muse optional-import control](../../../muse/evidence/verification-steps-2026-10-25T230230Z.json) | FAIL before preparation or runtime; no cloud resource created; original false cleanup flags retained |
| [Muse existing OSS route](../../../muse/evidence/verification-steps-2026-10-25T230409Z.json) | PASS: 6 named calls; controller 10 PASS / 0 FAIL / 0 SKIP; model NOT_RUN. Sandbox, template and private-cache absence were independently checked. The original upstream asset's 384,809,176 bytes and hash remain enforced. This does not replace the direct failure. |
| [Next-app corrected mode control](../../../next-app/evidence/verification-steps-2026-10-26T001520Z.json) | PASS at candidate `3db`, in 114.225 seconds: 6 named calls; controller 6 PASS / 0 FAIL / 0 SKIP; both owned absences. PR233's static audit of 232 COPY files is not 46 extra cloud passes. |
| [Public-main agents control](../../../agents-cli/evidence/verification-steps-2026-10-25T231923Z.json) | PASS at `c8`, in 27.299 seconds: 3 named calls; controller 19 PASS / 0 FAIL / 1 SKIP (model NOT_RUN); authentication, runtime-byte and CLI-I/O checks; both owned absences. One control, not 46 reruns. |

The frozen 207 calls plus the separate Muse OSS 6 and fixed next-app 6 account for 219 successful calls across different inputs and transports. This is not a rewritten all-green direct batch.

One further Muse operator diagnostic exited 1 after 49.615 seconds: expected build failure was observed, `diagnostic_collected=false`, one template and zero sandboxes. Output parsing yielded no diagnostic data, so no new network causality follows. Its original execution JSON contains a private machine path and remains unchanged outside publication; only an explicitly derived safe summary and hash appear in the canonical JSON. A separate [new-HOME typed E2001 absence check](../../../muse/evidence/muse-network-operator-20261026-independent-absence.json) confirms the exact owned template absent, without recovery deletes. This is not a template PASS or another native batch attempt.

## Reproduction, checks and limits

Follow [public launch testing](../../../docs/public-launch-testing.md) for exact workflow inputs, published installs and original cleanup assertions. [Native platform steps](../../../docs/platform-steps.md) describes the independent supplement and optional OSS requirements. Every receipt retains its exact attempt, commit, package identity and original bytes. Earlier failed and source-candidate evidence is unchanged.

Local verification completed: all 100 indexed original receipts (357,769 bytes) match their SHA256; all 46 default manifest digests and all 46 native recorded input-byte maps match the integrated source. Result, controller, call and cleanup totals recompute exactly. The existing fixed next-app proof and separate diagnostic absence hashes match. All 109 scoped files pass actual configured credential-value scanning with zero matches; original receipts contain no private-machine paths. Changes are only Markdown/JSON; no prior tracked evidence, runtime, manifest or recipe changed.

`python scripts/check_docs.py` checked 222 current documents with zero failures. The three record/index documents also pass. The managed-catalog checker reports zero violations, and `git diff --check` passes. The checker reused an existing dependency-complete environment without changing it. Initial default/PyPI-only verifier choices lacked yaml/jsonschema and did not run that checker. An early auxiliary scan iterated configuration names; the corrected verifier scanned actual credential values and passed all 109 files. These setup corrections do not change raw receipts or constitute product/cloud failures.

Normal latest-head CI and independent review remain required. This records task creates no cloud resource, installs no dependency and changes no runtime. Model/vendor-account skips remain unverified; smoke does not certify arbitrary PTY, GPU, desktop or production workloads. Issues 221 and 223 remain open because default Docker acceptance is still blocked.
