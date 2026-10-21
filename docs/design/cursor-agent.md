# cursor-agent

## Purpose

Run original pinned Cursor Agent through Agent Sandbox scalar commands. Intended for caller-owned disposable coding sandboxes, with an explicit permission opt-in. [Issue63](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/63).

## Capabilities

Original native planner/tools and original vendor account flow. Read-only version/package/headless diagnostics work without an account. Agent tasks require genuine CURSOR_API_KEY; no compatible-model/default operator-key routing. Only Linuxx64 is supported. Cloud Agents, enterprise schedulers, interactive/resume/MCP/plugins/delegation and other providers are unqualified.

## Exposed API

agent_version() -> fixed2026.10.19-6bbf2c4 string, after complete original-file identity; original --version. agent_native_check() -> booleans from original --help after hashes. agent_setup_check() -> settings presence/no values/network. agent(prompt:string required,cwd:string='',command_timeout:int=300,allow_unsafe_tools:bool=False,model:string='') -> buffered final/zero exit/identity/explicit permission/requested model; full types/ranges/errors in both READMEs.

Prompt1..32768UTF8bytes/noNUL; contained existing cwd<=4096bytes; deadline1..600/no bool; exactTrue permission required. Literal original argv --print/--output-format json/--disable-auto-update/--disable-project-configs/--sandbox disabled/--trust/--force/--workspace <project>, optional --model and prompt. No shell interpolation. Original final JSON result/success/is_errorFalse/nonempty text required; nonzero/invalid/truncated/timeout/overflow fail with sanitized error. Minimal native env/private per-call state,256KiB each stream, PIDFD/owner-marker cleanup and per-process serialization. External owned sandbox supplies isolation; same OS user remains.

## How to build

[Dockerfile](../../cursor-agent/Dockerfile), Alibaba generation2 base and non-root user, Python3.13. Original archive183733394bytes/SHA256cf80cc18d8b33bf33e762353977ca1868cfc45290c92c0ffdcef83bb8b37b44f; immutable official2026.10.19-6bbf2c4 URL. Digest controller-measured, not vendor-published. All460regular files/585886062bytes and notices preserved. Root-owned immutable /opt package, original bundled Node/launcher. Pinned server34e7e011... via server-sdk.commit/wheel or same immutable fallback. Default start/readiness on9000, no CMD/ENTRYPOINT. Native step preparation supports exact public ranges or an owned private OSS cache; unchanged300MiB/15000wire limits. Publish changed source/helper before preparation.

## Express feasibility

Feasible: slice

Limiting factor: authenticated vendor account and model egress are not available for verification.

Actual separate research runs unchanged original version/help and invalid-key refusal under Express UID1000. No KVM/Docker/GPU claim. New template requires its own non-root image, immutable steps/SDK create/fullHTTP/owned cleanup at exact source. Resource profile2vCPU4096MB,8GiB build ceiling; bundle585.9MB. Steps are not proof of Docker image cloud deployment.

## Risks

Native --force and disabled nested sandboxing require explicitTrue on an owned disposable target. Original tools can access same-user resources; this is not a tenant boundary. Only explicit CURSOR_API_KEY enters native env. Do not reuse Express/E2B/compatible-model credentials. No auth bypass. Private per-call config/cache/compile state removed; bounded descendants killed without touching unrelated processes. Vendor terms apply separately to authored Apache code; original notices preserved. No source/binary redistributed in Git.

## Test plan

L0: strict checker; authored argument/original-metadata/process/output/timeout/install-escape fixtures; real local HTTP with native absence explicitly skipped. L1: actual image/build/rootfs<=8GiB/non-root workspace and pinned native version/help. L2: published immutable native steps/officialREADY/actual SDK create/CLI+SDKsmokes plus full external16checks requiring actual original HTTP and SDK invalid-key refusal; independent fixture/process/private-cache/template/sandbox absence. Controlled invalid vendor key never comes from the operator. L3: only with real vendor credential and owned remote opt-in: existing source edit, unchanged original3test bytes, report/fresh nonce,3original+4held-outs/fresh post-returnACK. Missing keys remain NOT_RUN, never a model pass. L4: unrun/no provider claim.

Primary upstream references: [official installer](https://cursor.com/install), [headless](https://cursor.com/docs/cli/headless), [JSON format](https://cursor.com/docs/cli/reference/output-format), [vendor terms](https://cursor.com/terms-of-service). Pinned source bytes additionally verify hidden update/project-config flags. These docs are not evidence of an authenticated execution.
