# Express step payload and execution-profile verification

Date: 2026-10-19
Result: PARTIAL

## Scope

Follow-up on PR121's `8175b1927bd2ae2d8cba4c1e0de94cca65f2765d` with scoped
materializer, READY-diagnostic retention, private-journal cleanup, regression,
documentation and CI-download fixes. Runtime template sources remain unchanged.
New per-template receipts are retained at their existing evidence locations;
no original pass/failure is overwritten or converted into another outcome.

## Real platform findings

- A raw larger source payload is rejected by the actual Express service with
  `MicroSandbox steps is invalid: serialized JSON exceeds 16KiB`. No sandbox is
  created for those failed builds; the exact owned template is deleted and
  independently read back. These are failed builds, not failed model calls.
- Native ENV needs alternating key/value arguments, confirmed by the earlier
  failed and successful pilots. WORKDIR and USER are accepted by the service.
- Express begins build steps as `user`; a Dockerfile's dependency installation
  expects root. Without explicit USER root, actual apt operations fail on
  `/var/lib/apt/lists/lock` with permission denied. The corrected root-profile
  document build advanced beyond apt to source transfer, confirming that root
  installation works. That attempt subsequently failed on a GitHub raw-source
  connection reset; it is not recorded as a full pass.
- Inline compression permits the larger DeepSeek command source to deploy and
  pass real CLI/SDK smoke. Remaining over-budget profiles use only the immutable
  published checkout archive, with bounded download retries and SHA256 validation
  of each selected COPY file before writing. Small profiles prefer inline bytes
  so they do not add a source-download dependency. Temporary archives are removed.
- The corrected 24 local profiles fit the conservative 15,000-byte steps budget;
  preparation rejects an incompressible oversized input before any cloud call.
  This checks the wire format; it does not declare all cloud builds passed.

## Local checks

`python -m pytest -q scripts/test_prepare_steps.py scripts/test_check_docs.py
scripts/test_express_cleanup.py scripts/test_spec_tools.py`: PASS, 58 tests and
48 subtests. Real file-byte/mode reconstruction, archive integrity rejection,
size bounds, heredocs, unsupported/private inputs, exact provider status parsing
and independent cleanup gates are covered. Strict conformance again passed all
23 products plus skeleton. Current document and new-record links are checked
before publication. These tests do not run a model or use cloud mocks as a pass.

## Remote CI failure

The first PR121 local-e2e job failed before the test/checker stage because the
fixed Hermes source archive download returned HTTP429. The original failed run
remains history. The follow-up preserves the same source pin, adds curl's bounded
transient retries and downloads completely before extracting. This does not skip
Hermes or weaken any runtime gate. Current-head CI must pass before merge.

## Acceptance progress

The dated per-template receipts currently include real generated-step passes for
Python Hello, Node Web, Claude Code, DeepSeek Harness, Amp and Gemini. Other
attempts and corrected reruns remain in progress. No blanket all-template pass,
full-model L3, new Dockerfile L1 or completed original-64 roadmap is claimed.
Existing credentials remain local; private provider diagnostics/journals are not
committed or uploaded. All known failed pilot resources were reconciled by exact
ownership with independent absence readback.

## Persistent upstream archive throttling

The second current-head local-e2e attempt also failed before tests: all five
bounded codeload retries returned HTTP429. The next candidate uses the existing
actions/checkout mechanism for the identical public Hermes commit, explicitly
checks HEAD, disables persisted credentials, and retains frozen installation and
all Hermes tests. This changes source transport only; no runtime gate is skipped.
