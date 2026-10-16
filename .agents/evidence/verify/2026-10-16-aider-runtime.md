# Verification: Aider runtime

- Date: 2026-10-16
- Result: PARTIAL; actual CI image and real-model runtime PASS; canonical deploy-wrapper L2 remains pending.
- Change: [Issue 50](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/50).
- Base: Pi PR 86 current head `a361f490555ead0ff67081ffb4874abf292a1b2f`.

## Verified official inputs

Official PyPI aider-chat 0.86.2 metadata requires `>=3.10,<3.13`; the 0.86.2 wheel
is 377009 bytes. Metadata-only resolution on existing Python 3.11 found 108 compatible
wheel distributions / 118 MiB compressed. No complete dependency installation was
performed on the shared host. Official python-build-standalone 20260211 API assets
fix 3.12.12 and supply x86-64 SHA256
`1dbaa624a09e15afe7efbdac08d42993135a68db8d34f986ef6977a6d77bdc3c`
and aarch64 SHA256
`85fdc64fe672de7337198a63d89918037bf93bdb03480404d90f8f601abef1dd`.
Source links are in the design and both READMEs.

Pinned wheel source and configargparse 1.7.1 establish that defaults load before
explicit config paths. No official home/config-dir isolation switch exists.
No host or child HOME was replaced. Shared profile/store files remain untouched.

## Local checks

- `python -m pytest aider -q`:57 PASS in 7.55 seconds, including real Python child
  process cleanup, timeout/cancellation, explicit/default write behavior, stale
  edits, symlinks, private output, and real independent test-process controller
  negative controls. Fake executable/model fixtures do not prove upstream/model.
- `python scripts/test_spec_tools.py`:22 PASS in 8.606 seconds.
- `python scripts/check_template.py --all`:all 19 spec2 directories conform,
  zero spec2 failures. The scoped Aider checker also passes.
- Full `python scripts/run_local_e2e.py`:13 PASS /6 FAIL across19 templates;
  Aider is PASS. Unrelated failures remain visible and were not weakened or
  silently relabeled. Existing failures are actual CLI pin/setup mismatches in
  agents-cli/droid/opencode/qoder/qwen-code and missing real Chromium in
  browser-automation. These are not exact baseline-compared results; full normal
  remote CI must establish its supported environment independently.

The plain system Python checker initially lacked PyYAML; validation uses the
existing development venv with server/httpx/PyYAML. An early implementation syntax
mistake in a metadata-only size helper was corrected before producing any size
claim; no package download/install was counted from that failed invocation.

## Real source progress and cleanup

The first owned Express attempt downloaded only part of the official 32.3 MiB
Python archive because cloud GitHub transfer was slow. Aider never executed and
that sandbox was deliberately destroyed; the controller recorded FAIL rather
than a runtime pass. A second owned run transferred the identical official archive
after host SHA verification, deleted the host archive, reverified its SHA in cloud,
installed Python 3.12.12 and all 108 official Aider dependencies, and executed
actual Aider help with all required flags. Its later native-home negative-control
assertion failed before coding; that fixture used invalid empty explicit YAML
(`/dev/null`), so parsing failed before the intended default-key rejection. That entire
instance was destroyed. The third owned run checked fixture creation and again installed dependencies/
passed actual help, but retained that empty-YAML harness mistake and failed its
negative assertion before coding; it was destroyed. The fourth fresh owned run used a valid explicit `{}` config: actual official CLI
rejected the malicious native-home default even with the explicit override, and
actual slash/bang literal-input negative controls passed. Its later unselected-
path fixture incorrectly contained literal backslash-n sequences instead of a
multiline whole-file edit, so that assertion failed without reaching coding. The
whole owned instance was destroyed. The corrected reproducible runner now builds
a real multiline response, locally regression-checks its exact lines, and first
requires a positive selected edit before testing unselected refusals.
Actual coding evidence is added only after completion. No full 108-package download was
made on the shared host, and no shared HOME/store was changed.

## Remote CI and remaining gates

Initial head `3590cbac74c681eb2c8aeebe77f5006261fb1ac6` had four successful
remote checks, including [actual Aider image build](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/38854484890/job/116822849140).
Subsequent product and configuration/CI fixes received fresh CI. Head
`86f6076a137f54f51e9267decc446645d633ab0b` has four successful checks,
including [actual image build](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/38858795334/job/116836213684)
and both full local-e2e workflow jobs. The [regression job](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/38858795306/job/116836145714)
log was read with GitHub auth restricted to the API redirect: it contains the
scoped Aider pytest invocation and `57 passed in 6.87s`. Raw logs were not saved.
The records-only follow-up receives its own normal CI; image/runtime claims keep
their exact source and artifact provenance.

Actual native-home/CLI guards and configured final-image real coding now pass,
as recorded below. Canonical scripts/express_e2e.py → abx template deploy L2
remains pending, and other providers are unverified. No tested_on promotion;
the PR remains draft under the explicitly requested draft delivery scope.

## Independent review corrections

Peer `remaining_templates` reviewed official PyPI wheel source and reproduced two
concrete upstream behaviors: yes-always can touch an unselected external path
before git rejects it; message-file prompts starting `/` or `!` dispatch commands.
The wrapper now pins `yes-always: false` without an auto-yes argv flag and prefixes
message-file input with literal text before the original prompt. Selected paths
are precreated, so explicit selected editing needs no create confirmation.
The peer independently reviewed both fixes and reran 55 regressions successfully.
`aider/verify_upstream_guards.py` is a reproducible actual-installed-CLI loopback
model negative-control runner; its deterministic model is not real-model coding
acceptance. No default HOME value or shared profile/store is changed.

Official configargparse 1.7.1 was also executed directly with Aider's store_true/
default=None action and YAML `yes-always: false`: the result is None, not False.
Upstream EOF consequently still accepts default Yes. The wrapper now keeps a
continuous No stdin feeder alive until actual process exit, then reaps/joins it
after owned group cleanup. The 57 local regressions include 100000 confirmations
without EOF plus leader exit, timeout and cancellation with that feeder active.
No successful real CLI negative/model result is inferred from the earlier
config-only fix.

The fourth source sandbox's read-only native platform inspection established
Debian 13 and system Python 3.13.13; the independent Aider runtime remained
Python 3.12.12. No system interpreter, HOME value or shared store was replaced.
Head `3de9aaeddcd01befb24b81d9275b901b580f5ad2` also had all four remote
checks succeed (including actual image build), before the continuous-No/input
fix in the next source head. Its archive metadata is artifact `12027335721`,
472704050 bytes, run `38855333392`; no archive SHA is claimed from metadata.
A small log-artifact download attempt returned HTTP401 and was not retried.

## Continuous regression coverage correction

Final review identified that the shared e2e workflow explicitly listed each
existing template's regressions but did not yet run Aider's 57 tests. The four
successful checks on product head `ecbabafca49fd8f5d0cf980842a7fa69ee66d7c6`
therefore establish its actual image and HTTP L0 checks, not remote execution of
all 57 Aider regressions. Add the scoped Aider pytest row to the existing e2e
workflow; no image selection/build contract changes. Fresh CI for that coverage
change must pass. Product commands/runner bytes remain frozen to the reviewed
image source. Root independently reviewed final process, file, literal-input
and deterministic actual-CLI guard paths; live results remain separate gates.

## First final-image run: FAIL, all owned cleanup PASS

[Immutable failed run](../../../aider/evidence/image-runtime-2026-10-16-attempt1.json)
uses actual image artifact `12026949932`, run `38856361807`, product source
`ecbabafca49fd8f5d0cf980842a7fa69ee66d7c6`, archive SHA256
`13006e0577a904435eb7384698d8530bce82f08d1abe8ceb12372c3984076cd0`.
The archive was downloaded/SHA-verified/pushed inside an owned Express helper;
only small ZIP manifest ranges reached the host. Official generation-2 template
registration and READY passed. All 56 installed server module hashes matched
pinned SDK `e2cb27e24fde0a67112f82b8d44af463445a5d1a`; actual SDK/HTTP/CLI
Aider version passed, with the non-model external suite 9 PASS / 1 explicit SKIP.

Actual official CLI selected whole-file editing and slash/bang literal-input
controls passed. The first absolute-path artifact-state assertions passed, then
an overly specific `Skipping edits to` text assertion failed; later relative and
existing-file cases were unrun in that attempt. The corrected guard requires
actual artifact state, model-call occurrence and the selected positive parse,
with fixed-category diagnostic booleans for upstream refusal/path-error text.
It does not infer that every outside-path case reached confirmation logic.

The model HTTP suite reported 9 PASS / 1 FAIL: the prewarmed port-9000 target
lacked compatible settings, so no real model call occurred. Create-time envd
settings do not update that already-running process. The documented correction
uses public `commands.start(env=...)` to start the installed original image server
on port 9010, consumes its process stream, and verifies configured target state
via SDK/HTTP/CLI before model execution. No product source overlay or HOME change.
The English/Chinese examples now show that activation, port and owned cleanup.

Both runtime instances and the transfer helper were killed and absent from
scoped list readback. The template was deleted and absent; official ACR tag and
repository deletion were verified HTTP404. No failed-run resource was reused.
The retry uses a new unique repository, template name and private per-run journal.

## Configured actual-image retry: PASS

[Immutable configured run](../../../aider/evidence/image-runtime-2026-10-16-configured.json)
uses the same reviewed actual image archive/source as attempt 1, with a fresh
owned repository/template/instances and explicit native-process configuration.
No commands.py was copied over the image; its SHA256 matched reviewed product
source. All 56 server modules matched pinned SDK source. SDK/HTTP/CLI version
smoke passed; the non-model suite was 9 PASS / 0 FAIL / 1 intentional SKIP.

The new port-9010 server was started from the installed image commands using
public SDK commands.start with only explicit Aider settings/workspace in env.
Its stream was consumed; credentials were not placed in argv/files and HOME was
unchanged. SDK/HTTP/CLI target setup all required key/base/model booleans true.
Actual upstream home-default rejection and deployed wrapper refusal both passed.
Actual official-CLI loopback selected editing, slash/bang literal text and all
three external-path artifact-state controls passed. Diagnostics showed explicit
refusal text only for the relative path, an upstream path-error category for
the existing absolute file, and neither fixed marker for new absolute output.
Artifact state is the acceptance boundary; no universal No-feeder branch claim.

Real qwen3.8-flash HTTP model acceptance: 21 PASS / 0 FAIL / 0 SKIP. The seeded
calculator failed before edits; default ask preserved bytes; coding changed
calculator.py and created REPORT.md plus the exact artifact. Original tests were
unchanged, all three independent unittests and six held-out calculations passed,
and artifacts were retrieved through the target files API. Model completion
without those observable changes was not accepted. Native image Node was
independently read as v20.20.2; base system Python remains 3.13.13 and Aider uses
its separate verified 3.12.12 runtime.

All ten cleanup flags are true: transfer helper and both runtime instances
killed/absent, template deleted/absent, official ACR tag and repository HTTP404.
The first failed image report remains immutable. Root independently reviewed
final commands/guard code before the actual pass. Current design/status remains
proposed/experimental and PR draft because canonical scripts/express_e2e.py →
abx template deploy L2 and other providers remain unverified. No canonical
express-YYYY-MM-DD.json or tested_on promotion is produced from this supplement.
