# Verification: Aider runtime

- Date: 2026-10-16
- Result: PARTIAL; real source and image gates are ongoing.
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

- `python -m pytest aider -q`:55 PASS in 7.41 seconds, including real Python child
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
assertion failed before coding; the fixture creation return code was not checked,
so that failure does not establish whether defaults were bypassed. That entire
instance was destroyed. A third fresh owned run corrects and checks this fixture
and adds actual installed-CLI loopback controls before real-model acceptance.
Actual coding evidence is added only after completion. No full 108-package download was
made on the shared host, and no shared HOME/store was changed.

## Not yet verified

Initial head `3590cbac74c681eb2c8aeebe77f5006261fb1ac6` had four successful
remote checks, including [actual Aider image build](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/38854484890/job/116822849140)
and both local-e2e workflow runs. Subsequent peer-review fixes require fresh CI.
Actual config negative controls and real-model coding acceptance remain pending. No provider is listed as tested_on, no named-template image L2 READY is
claimed, and L4 providers remain unverified. The PR must remain draft.

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
