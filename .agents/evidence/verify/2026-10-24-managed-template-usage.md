# Managed template guide and default entry verification

Result: PARTIAL — real isolated Docker job and normal PR checks pending.

- Existing managed catalog and safe diagnostic regressions: 22 tests passed.
- Managed catalog: zero violations; historical JSON unchanged.
- Documentation: 222 documents, zero broken local targets.
- All ten Python examples in eight bilingual README files parse.
- Specification tools: 58 tests passed; full template checker: zero failures.
- No new E2B live run. Its guide retains that concise boundary.
- Current native fixture will install paired client/server 0.3.1a5 from public PyPI,
  validate installed versions, use current fixed provider/CLI sources, and verify
  default exec separately from explicit-entrypoint upstream interpreter sessions.

Real Docker result will be appended as a new dated receipt after execution. The
2026-10-21 historical native receipt is not rewritten or presented as this run.

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
