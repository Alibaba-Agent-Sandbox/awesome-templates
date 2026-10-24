# Managed template guide and default entry verification

Result: PASS for the recorded real managed runs and local checks. Final PR-head CI and merge are tracked separately.

- Existing managed catalog and safe diagnostic regressions: 22 tests passed.
- Managed catalog: zero violations; historical JSON unchanged.
- Documentation: 222 documents, zero broken local targets.
- All ten Python examples in eight bilingual README files parse.
- Specification tools: 58 tests passed; full template checker: zero failures.
- No new E2B live run. Its guide retains that concise boundary.
- Current native fixture will install paired client/server 0.3.1a5 from public PyPI,
  validate installed versions, use current fixed provider/CLI sources, and verify
  default exec separately from explicit-entrypoint upstream interpreter sessions.

The 2026-10-21 historical native receipt is not rewritten or presented as this run.

## Published Express CLI and Python checks

[New independent receipt](2026-10-24-managed-public-cli.json): both base and
code-interpreter-v1 passed public CLI 0.4.16 positional create with detach and a
180-second timeout, documented exec yielding 42, public Python 0.3.1a5 files,
explicit ProviderSandbox.run_code E8004, CLI kill without -y, and independent
SDK NotFound. No shell fallback is claimed for the current provider interface.

## First current-provider native attempt

[Run 40119215984](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/40119215984)
failed default exec with HTTP 400: its retained historical execd v1.1.0 requires
the retired command field, while the current provider uses argv. The created
default instance was independently absent via SDK and Docker; provider engine
and local server shutdown passed. Native interpreter execution was not reached.
The [failed receipt](2026-10-24-managed-native-attempt-1.json) is preserved.
The fixture now uses the same digest-pinned release-1.1.1 execd as current provider
acceptance; no provider fallback or protocol change is introduced.

## Corrected current-provider native run

[Run 40119588624](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/40119588624)
at templates `85d7ab057b0136e82cd966a397fe268556ef61f3` passed all 29 checks. The
[new receipt](2026-10-24-managed-native-pass.json) records the exact fixed CLI,
provider and upstream source, public client/server 0.3.1a5, runtime image identities
and digest-pinned release-1.1.1 execd. The CLI is built from fixed release source
for its provider engine; this job does not claim public npm installation.

A first instance used the catalog default image with no native interpreter
entrypoint override, ran Python yielding 42, and was independently absent via SDK
and Docker. A separate explicit-entrypoint instance passed shell/files, upstream
SDK connection to the same ID, Jupyter health, native 37→42 persistent context,
context isolation, program errors and context deletion. Project ProviderSandbox
run_code still returned E8004, as expected; upstream SDK success does not add that
unified provider operation. The second instance, provider engine and local server
were all confirmed cleaned up.

Two already-started documentation-head runs used the same old execd fixture and
failed identically before native execution: [40119293843](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/40119293843)
and [40119398724](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/40119398724).
Their [second](2026-10-24-managed-native-attempt-2.json) and
[third](2026-10-24-managed-native-attempt-3.json) receipts preserve the original FAIL
and independently confirmed default-instance and local-process cleanup. No active
owned test was cancelled to hide a failure.
