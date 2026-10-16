# Decision: Ship real pinned coding CLIs behind the restricted Agents session API

Status: proposed

## Problem

The agents-cli placeholder installed no upstream CLI and automatically prepended
synthetic executables when model testing was disabled. A passing local turn could
therefore be mistaken for product acceptance. Its Dockerfile/template/docs also
predated v2 requirements. Importing a policy in commands.py alone does not apply
that policy to canonical serve, which resolves its own policy after imports.

## Decision

Ship exact Codex/Qwen versions and a keyless actual-version diagnostic. Preserve
the small session/runtime surface through one checked-in endpoint allowlist for
both startup modes. The canonical start command passes --policy explicitly;
direct startup loads the same file using the SDK's supported string path.
Disable general shell/files/process/model routes. Default e2e diagnoses the actual
CLIs and checks HTTP/session contracts without submitting a turn. Synthetic
adapters are restricted to explicit test child PATHs and are not copied into the
image. Migrate to the required base/non-root/generation-2 v2 anatomy and bilingual
documentation.

## API Design

`agents_version() -> str` executes exact pinned CLI version checks and returns
`codex 0.162.1; qwen-code 0.23.0`. Missing/wrong versions, nonzero exit and timeout
raise sanitized RuntimeError. The policy opens list_commands, run_command and
six Agents session/runtime endpoints; remaining endpoints return404.

The implemented runtimes are codex and qwen-code. Event202 acknowledges queueing,
not model success. Sessions/items live in this server process. Generic SDK
files/process and delete/cancel/update/SSE are outside this template's allowlist.
This changes the former placeholder to version2.0.0; runtime keys remain external.

## Alternatives considered

Retaining automatic fixture selection would preserve false product passes.
Relying only on Docker's policy environment would leave standalone canonical
startup dependent on external configuration. Reopening file/shell endpoints to
make L3 testing easier would change the intended restricted API. Instead, leave
L3 explicitly incomplete until a separate authorized out-of-band verifier exists.

## Dependencies

[Issue #25](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/25),
pinned @openai/codex0.162.1, @qwen-code/qwen-code0.23.0 and the python-sdk server
archive commit in Dockerfile. Shared catalog/CI integration belongs to the owner
coordinating this contribution. Actual model credentials and independent artifact
verification remain prerequisites for coding acceptance.

## Test Strategy

Real SDK HTTP subprocesses exercise both direct and exact template start_cmd
forms. Explicit fixture PATH tests verify both adapters' two-turn event/item
protocol, correct/missing/wrong token authentication, closed endpoints, no implicit
fixture fallback with an empty PATH and sanitized diagnostic failures. Separately,
real pinned CLIs run version/HTTP checks with no model turn; requesting required
model acceptance must exit1 rather than infer a pass. Checker, docs/links/records
and scoped diff validation complete local conformance.

## Acceptance criteria

- v2 anatomy, exact pins, non-root base, generation2 startup and bilingual docs.
- Direct/canonical startup enforce identical allowlist and server authentication.
- No E2E_RUN_LLM flag can silently activate synthetic production executables.
- Real CLI diagnostics/local HTTP and explicit fixture protocol regressions pass.
- Real-model/image/cloud acceptance remain separate requirements, with no provider
  verification or official status inferred from local or fixture runs.
- Normal owner Issue/PR/CI/review/verified merge gates remain required.

## Evidence

[Local verification](../../../evidence/verify/2026-10-16-agents-cli-restricted-runtime.md).

Image dependency follow-up: Qwen0.23.0 requires Node>=22. The image now installs the reviewed SHA256-verified official Node24.16.0 archives; shared host CI Node24does not establish image compatibility. [L1 gate preparation](../../../evidence/verify/2026-10-16-template-image-build-gate.md).
