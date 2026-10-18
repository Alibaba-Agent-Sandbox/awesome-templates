# Gemini CLI template usage

The maintained usage contract is in the template's [English README](../gemini/README.md) and [中文 README](../gemini/README.zh-CN.md). They include deployment, CLI, Python SDK, direct HTTP POST, typed parameters, authentication, deadlines, tool permissions, errors, development and contribution instructions.

Gemini CLI remains pinned to `@google/gemini-cli@0.64.0`. The template now uses the Alibaba base, generation 2, `/home/user/app` and non-root `user`; it has no image CMD/ENTRYPOINT. `gemini_setup_check` and `gemini_version` are read-only diagnostics. The named `gemini` command defaults to upstream read-only plan mode; set `yolo=true` only for an authorized coding task. `cwd` must resolve inside `WORKSPACE`.

`GEMINI_API_KEY` must be a real Gemini-compatible key. Missing keys fail before CLI launch; an OpenAI key is not substituted. Setup never rewrites user configuration. Keep server and provider gateway authentication separate.

Acceptance now requires fixing an existing source file, new artifacts, original tests preserved, independent target-side tests and held-out checks. A response containing `ABX_E2E_OK` alone cannot pass. Forced-off L0 invokes no model; a missing key blocks required L3. No provider acceptance is claimed until passing evidence exists. See [design](design/gemini.md) and [verification](../.agents/evidence/verify/2026-10-16-gemini-runtime.md).
