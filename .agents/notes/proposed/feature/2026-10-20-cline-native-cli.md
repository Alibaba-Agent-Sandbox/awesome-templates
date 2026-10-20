# Decision: genuine native Cline CLI with explicit compatible provider

Status: proposed

## Problem

[Issue66](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/66) requests actual Cline CLI, not its editor extension or a similarly named package. Need pinned source/license/argv/SDK/Express/real coding acceptance. Host execution of model-generated code and shared developer credentials are excluded.

## Decision

Install official npmcline3.0.73 with full integrity lock and unmodified Linuxx64/Bun binary; require its exact SHA256 and Node24.16.0. Native headless JSON/yolo via stdin with explicitly configured approved compatible provider/model/base, no Cline hosted login. Own HOME/config/data/session/team/MCP state per call, no global credentials/updates/telemetry/logs. Retain native tool authority honestly rather than implying cwd is a security boundary.

## API Design

Version, presence-only setup and cline(prompt,cwd='',command_timeout=300), all scalar. Bound UTF8/prompt/path/time/output and resolved cwd. Model key only native OPENAI_API_KEY env, no wrapper settings/argv key. JSON result retains native exit/stdout/stderr/version; independent L3 requires a real completed run_result and original/source/artifact/held-out proof, not a marker. Serial lock plus owned group/marker/pidfd cleanup and private settings deletion on all paths.

## Alternatives considered

Survey extension version is not the native CLI version. Actual npmcline3.0.73 and its help/tag were inspected; another package exports a different command. A chat wrapper/version-only/fake CLI cannot qualify coding. Unrestricted host model execution, invented flags/vendor key, shared user config or silent provider fallback are excluded.

## Dependencies

Official npmcline3.0.73 and core packages0.0.95 locked; actual nativeSHA2561ff8841d17d4d83763134c193d414e4f7fcf2ef56af759e5ebbe96727fc2c8f7. Source cli-v3.0.73 commitc718573538d76310f464541617ab665108a6c999, Apache2.0retained. Official SHA256Node24.16.0, servere2cb27e; paired operator SDKd4d93e8c and verified nativeCLI0.4.1 for cloud. Existing approved OpenAI-compatible model endpoint/key only.

## Test Strategy

Local authored argument/config/symlink/private profile/credential/stdin/nonzero/redaction/cleanup/serialization tests. Exact native terminal NDJSON parser rejects incomplete/aborted/error/marker-only outcomes; generated-code controller refuses loopback. Actual keyless version/help only pin proof. Then real image L1, SDK-created canonical native steps, actual model source/report/exact artifact/original test byte identity/complete original3tests/held-out post-return ACKs inside fresh owned cloud target, independent own project/listener/native private state/outer sandbox/template absence.

## Acceptance criteria

All source/catalog/spec/docs/record/latest CI gates pass; actual native L1 and current Express SDK create/commands/model/independent cleanup receipts with exact provenance. Complete bilingual user docs and actual normal PR/main merge before Issue66closure. Missing/skipped/failing native/model gates remain explicit.

[Verification](../../../evidence/verify/2026-10-20-cline-native-cli.md).
