# claude-code

## Purpose
Run unchanged original Claude Code2.0.76 tools through named SDK/HTTP calls. Preserve legacy Anthropic-oriented API and add explicitly configured experimental compatible text/tool transport. [Issue15](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/15).

## Capabilities
Original headless planning/Read/Edit/Write/Bash tool execution, bounded per-call owned state, artifact retrieval. Authored Messages/Chat adapter translates text/tool wire schemas, not planning/execution. Anthropic does not support non-Claude routing; original subscription, image/thinking/MCP/plugin/delegation/resume compatibility is not asserted.

## Exposed API
Legacy claude/version signatures preserved. New claude_byok(prompt,cwd='',command_timeout300,allow_unsafe_tools=False) -> buffered native completion metadata/final text; timeout integer1..600, cwd existing/contained, prompt1..32768UTF8/noNUL. Native/check setup only fixed identity/help or presence/no values. [Complete contracts and constraints](../../claude-code/README.md#command-reference).

## How to build
Alibaba generation2basev0.0.49/non-root; original npm2.0.76/SHA512 exact lockfile with npm ci --omit=optional --ignore-scripts; root-owned original cli.js verified SHA256 at first/stat-changed use. Base Node20 supports upstream Node>=18. Preserve upstream license/ripgrep notices. Server34e7e011... optional explicit pin and immutable fallback. No image cloud deployment claim from native steps.

## Express feasibility
Feasible: yes

Limiting factor: explicit approved model transport and real acceptance pending

Headless text/tools require no nested privileges/display. Existing approved Messages endpoint404 cannot support direct native transport; authored text/tool adapter targets only explicitly configured approved Chat origin. Native synthetic then genuine coding/independent tests must pass before current provider qualification. Declared2CPU2048MB is not measured peak memory.

## Risks
Original code and generated tools execute only on an owned disposable target. Minimal native/tool environment contains no actual root/model/cloud/GitHub credential, only ephemeral local adapter token. Private HOME/config/cache, no session persistence, hooks/project settings disabled, only four native tools. Same-user OS access remains; no tenant boundary claim. Bounded output/request/response/native turns/deadline/RPC drains and independent own process/listener absence; redirects/unsupported content fail closed. Legacy behavior remains separate and unqualified by new isolation evidence.

## Test plan
Fixed non-executable transport fixtures verify text/schema/tool identities, actual usage/native SSE, unsupported model/path/auth/content/thinking/tool refusal, redirect prevention and own listener cleanup. Authored process fixtures verify bounded output/timeout/descendants and preserve unrelated processes. Canonical published-source steps -> officialREADY -> actual SDK Sandbox.create -> CLI/SDK hash/version/help and complete HTTP -> synthetic original native routing before key -> original native coding -> changed source/original3test bytes/report/exact nonce/original3+4held-outs/fresh post-returnACK -> private/process/project/listener/cloud/template/OSS absence. Independent non-root L1 image, spec/strict/docs/records/latest CI and normal reviewed merge remain required.

Current1.3.0 explicitly requires allow_unsafe_tools=True before any model call, selecting original --dangerously-skip-permissions inside the owned disposable outer sandbox with only Read/Edit/Write/Bash visible. Original legacy claude remains dontAsk. Native tool permissions are configuration, not an OS tenant boundary; all strict completion/artifact/cleanup gates stay required.

Template1.3.1 distinguishes only a SHA256-bound original optional Bash file-path request peer disconnect from failed required delivery. No cancelled response is counted completed; required delivery plus independent original/held-out source tests remain acceptance requirements. Unknown auxiliary/main/network/upstream failures remain fatal.
