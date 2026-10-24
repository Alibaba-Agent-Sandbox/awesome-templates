# Public launch diagnostic follow-up

Result: PARTIAL

Scope: `fix/public-launch-diagnostics`, acceptance runner and evidence only.
Local environment: Python 3.13. PASS: 16 runner regressions; 44 specification-tool tests; 222 Markdown documents with zero link failures; Python compile; diff check.
The real follow-up run is not yet executed at this checkpoint.

The first [pilot run 40107869809](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/40107869809)
used templates `295aff8f45f710eadf46d164b7ce4150b2c914ec`, CLI
`25e22d8f5c38bb0b7636ba699511da4f4695ec48`, paired Python SDK
`6398c6fdd777ff6c8ae9c7b2acb4cc52d457a633`, and provider
`4b4027cac0ec145aa89bdddda36cf8f7268c8d0e`. It installed a packed candidate CLI,
candidate SDK, and local provider checkout; this is not public-index installation evidence.

- Express: all application assertions passed, including host CLI/Python/HTTP expected
  results, negative authentication, source identity, process execution, and files.
  Overall FAIL: one prepared cleanup check failed. The sandbox was confirmed absent.
- OpenSandbox with server proxy explicitly enabled: CLI template launch exited 2;
  overall FAIL. Sandbox and prepared artifacts were independently confirmed absent.
  The old error report cannot establish the underlying startup/binding cause.
- A subsequent independent Express native inventory found no `public-e2e` template
  aliases and no matching tags in the `python-hello` ACR repository. No destructive
  action was taken. This does not retroactively change the original failed report.

Original sanitized reports and the separate inventory readback are preserved in
[the pilot evidence directory](2026-10-24-public-launch-pilot/). No raw CLI logs,
credentials, or native resource identifiers are included. The exact failed cleanup
operation was not recorded by the old runner; this change makes future failures diagnosable.

The follow-up default matrix explicitly selects OpenSandbox direct mode and records that mode in its report. It does not overwrite the failed proxy run or constitute proxy acceptance. A separate provider native probe checks actual direct/proxy authentication on the same owned sandbox.

Follow-up local validation: 19 runner tests pass after aligning manual HTTP requests with the already-supported X-Access-Token header. New regressions preserve gateway headers case-insensitively, prohibit overwriting gateway Authorization, and ensure both application headers are invalid in negative authentication. This newer request code still requires a new exact-ref live receipt; the prior pilot2 report remains tied to5d70861.

Final matrix preparation: public package installation replaces repeated source builds, with fixed-ref version extraction and installed-version checks. This is pending the new versions being published and a new public-install pilot. Negative authentication explicitly preserves a pre-existing mixed-case gateway X-Access-Token.

Local follow-up: 20 runner tests, workflow YAML parse and diff checks PASS after public package installation preparation. Full public-install pilot remains pending publication.

Public-install workflow explicitly selects npmjs.org and PyPI and verifies actual installed metadata. Each sanitized attempt includes the package versions and fixed source refs selected by this workflow. Local fixed-ref version extraction passed for CLI0.4.16 and SDK0.3.1a4; this does not assert their publication.
