# Canonical Express cleanup outcome regression

Date: 2026-10-16
Result: PARTIAL

## Reproduction and scope

Actual old harness at `a361f490555ead0ff67081ffb4874abf292a1b2f`, invoked with
synthetic CLI/SDK callbacks: deploy READY, create success and smoke match, followed
by kill exit 1, returned 0 and created an `express-2026-10-16.json` provider-pass
file. The temporary reproduction directory was removed. No cloud resource or
model call was created. This is a real harness defect demonstrated with fixtures,
not proof of a real provider cleanup failure.

Scoped product changes: canonical runner, its established spec-tools test entry
point, new cleanup unittest slice, contribution instructions, English/Chinese
specification clarification and owner records. No template runtime, Dockerfile,
catalog, provider-pass file or CI workflow is changed.

## Executed checks

- PASS: `python scripts/test_spec_tools.py`, exit 0, 31 unittest methods including
  cleanup subcases. The initial version passed 31 parametrized pytest cases;
  tests were then expressed as standard-library unittest so the existing CI
  entry point includes them without a new dependency. The final 31-method run
  includes actual redirected-descendant completion and SDK pagination fixtures.
- Independent source review found that rejected/failed preflight still called
  process/marker cleanup and could mutate a pre-existing alias's work. Fixed:
  those mutators require confirmed ownership and an actual deploy attempt.
  Regressions prove neither mutator runs on pre-existing/failed preflight; a
  concurrently created unowned marker is preserved. The existing one-CLI-call
  pre-existing-alias assertion remains intact.
- Self-review additionally fixed unknown-create ordering: preserve the known
  template until SDK sandbox reconciliation, rather than delete the alias anchor
  first. A negative regression proves no direct delete precedes recovery.
- PASS: kill/delete nonzero and exceptions cannot write pass evidence or return
  0, even when the recovery fixture succeeds. Private failure intents remain.
- PASS: success publishes only after both cleanup calls; exact alias recovery
  excludes an unrelated template. Unknown deploy/create plus empty inventory
  remains unresolved. SDK recovery paginates and kills only owned instances.
- PASS: real local Linux leaders exiting 0 and 7 leave no redirected descendant
  marker after the cleanup deadline. Existing idle/wall/progress/push-lock tests
  also pass. WNOWAIT holds leader identity until group kill and reap.
- PASS: strict checker, 18 conformant directories and zero failures; all 19
  relative links in scoped docs resolve; three Python sources parse; scoped
  `git diff --check` passes. Configured-secret scan runs on the staged scope.

## Honest limits and cleanup

Maintenance clarification: both a361 and the initial cleanup fix already passed
`--acr-repo <owned-alias>` and an explicit derived tag, so the reviewed heads did
not use catalog repository/latest defaults. The follow-up makes the tag `review`
and records `acr_repo`/`acr_tag` in plan/private intent; regressions assert actual
deploy arguments. This is intent clarity, not evidence of a prior overwrite bug.

All CLI/SDK cloud operations in these unit tests are explicitly synthetic or
patched; no Express/Docker/model acceptance is claimed. Actual canonical deploy,
official alias lookup, lost-response cloud recovery and provider smoke have NOT
RUN for this revision. No cloud credentials were uploaded or stored. Native
provider L4 and deliberate process-group escape remain outside scope.

Private failed intents are retained intentionally by the product. Test-owned
fixture roots clean their own intents; the older fixture cases can leave small
synthetic failure-intent files outside the checkout, containing no secrets or
real resource IDs. No broad temporary-directory deletion is performed.

Reference: [Issue 90](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/90).
