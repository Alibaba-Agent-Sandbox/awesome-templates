# Verification: Aider runtime

- Date: 2026-10-16
- Result: PARTIAL; real source and image gates are ongoing.
- Change: [Issue50](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/50).
- Base: Pi PR86 current head `a361f490555ead0ff67081ffb4874abf292a1b2f`.

## Verified official inputs

Official PyPI aider-chat0.86.2 metadata requires `>=3.10,<3.13`; the0.86.2 wheel
is377009bytes. Metadata-only resolution on existing Python3.11 found108 compatible
wheel distributions /118MiB compressed. No complete dependency installation was
performed on the shared host. Official python-build-standalone20260211 API assets
fix3.12.12 and supply x86-64 SHA256
`1dbaa624a09e15afe7efbdac08d42993135a68db8d34f986ef6977a6d77bdc3c`
and aarch64 SHA256
`85fdc64fe672de7337198a63d89918037bf93bdb03480404d90f8f601abef1dd`.
Source links are in the design and both READMEs.

Pinned wheel source and configargparse1.7.1 establish that defaults load before
explicit config paths. No official home/config-dir isolation switch exists.
No host or child HOME was replaced. Shared profile/store files remain untouched.

## Local checks

- `python -m pytest aider -q`:52 PASS in7.42seconds, including real Python child
  process cleanup, timeout/cancellation, explicit/default write behavior, stale
  edits, symlinks, private output, and real independent test-process controller
  negative controls. Fake executable/model fixtures do not prove upstream/model.
- `python scripts/test_spec_tools.py`:22 PASS in8.606seconds.
- `python scripts/check_template.py --all`:all19 spec2 directories conform,
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

The first owned Express attempt downloaded only part of the official32.3MiB
Python archive because cloud GitHub transfer was slow. Aider never executed and
that sandbox was deliberately destroyed; the controller recorded FAIL rather
than a runtime pass. A second run transfers the identical host-downloaded official
archive after SHA verification, deletes the host archive, verifies it again in
the owned sandbox and installs the fixed runtime. Installation/coding evidence
will be added only after actual completion. No full108-package download was
made on the shared host, and no shared HOME/store was changed.

## Not yet verified

Actual completed Aider help/config/model acceptance and actual image CI are
pending. No provider is listed as tested_on, no named-template image L2 READY is
claimed, and L4 providers remain unverified. The PR must remain draft.
