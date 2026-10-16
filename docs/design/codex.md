# codex

## Purpose

People who want OpenAI Codex CLI inside an Agent Sandbox, without a TUI, run this template. The sandbox installs pinned `@openai/codex` and exposes non-interactive `codex exec` (JSONL events, sandbox and approval selection, model, working directory, resume), plus config and `AGENTS.md` helpers. The model key stays in the environment.

## Capabilities

After the server is READY the sandbox can:

- Report the CLI version (`codex --version`).
- Probe whether Codex's own Linux sandbox can start, and say which bypass flag to use when it cannot.
- Run `codex exec` and return the JSONL events (`thread.started`, `turn.*`, `item.*`, `error`) plus the last agent message and `thread_id`.
- Resume a previous exec session with `codex exec resume <id>` or `codex exec resume --last`.
- Write `$CODEX_HOME/config.toml` for an OpenAI-compatible `base_url` (DashScope-style `/compatible-mode/v1`, or `ABX_LLM_BASE_URL` / `OPENAI_BASE_URL`). Codex 0.162.1 accepts only `wire_api = "responses"`. `wire_api = "chat"` is rejected by the CLI.
- Write `AGENTS.md` into the working directory. Codex reads that file as project instructions. This template does not replace it with `model_instructions_file`.

Express slice: the CLI itself runs. Its nested Linux sandbox often does not. See Express feasibility.

The legacy command `codex` remains as an alias of `codex_exec` with `prompt` and `model` only. Codex 0.162.1 rejects the old argv `codex -p <prompt> --model <model> --yolo --output-format json` (`--output-format` is an unexpected argument). `--full-auto` is also rejected. `--yolo` is a hidden alias of the bypass flag on `codex exec`; the template passes the documented long flag instead.

### apply-patch (separate template)

Survey section `docs/template-market-survey-2026-10.md#apply-patch` (issue #60, batch 2, P1). That template is a file tool, not another coding CLI. OpenSandbox's page (fetched 2026-10-15) describes compiling `codex-apply-patch` from an `openai/codex` commit. `CODEX_REF` in that doc is still a placeholder, and `examples/` has no `apply-patch` directory. The headless call is `apply_patch < /tmp/change.patch`. Express feasibility there is partial until a commit is pinned; the resulting binary does not need Docker or KVM. Build memory is the heavy part; runtime is 2 vCPU. Named command in that template: `apply_patch`. It does not depend on this directory.

This template does not build `codex-apply-patch`. Codex CLI 0.162.1 still has in-agent patch tools (`apply_patch_freeform` is present in the linux binary). Those run only as part of `codex exec` when the model edits files. They are not the standalone `apply_patch` binary #60 is for.

### codex-agent-api (issue #23)

`codex-agent-api` overlaps this template only on the CLI. It is a different control plane: an HTTP service shaped like the OpenAI Agents API (`/v1/agents/sessions` and related routes) that starts a Codex subprocess per turn. The backlog entry depends on `codex` and its survey section says the Agents server is started by a named command, not by `start_cmd`.

The directories should not be merged. This template is the place for `codex exec`, version, setup, `config.toml`, and `AGENTS.md`. Issue #23 owns session lifecycle, streaming Agents API responses, and artifact routes. Its current `commands.py` still calls the legacy `codex -p ... --output-format json` argv, which 0.162.1 rejects, and it does not share this template's sandbox probe. When #23 is rewritten it should pin the same `@openai/codex@0.162.1` and use the same bypass and provider-config behavior. It should not reimplement them as a second coding-agent template.

## Exposed API

Upstream binary: `codex` from `@openai/codex@0.162.1` (`codex-cli 0.162.1`). A non-zero exit raises `RuntimeError`. Secrets are not placed in argv or in `config.toml`.

### codex_version

| | |
|---|---|
| Parameters | none |
| Returns | string, the `X.Y.Z` token from `codex --version` |
| Argv | `codex --version` |

### codex_setup_check

| | |
|---|---|
| Parameters | none |
| Returns | object (probe result, no secret values) |
| Argv | `codex --version` and `codex sandbox --permission-profile :read-only -- true` |

Fields include `binary_present`, `version`, `pinned_version`, `linux_sandbox`, `sandbox_error`, `bwrap_path`, `bwrap_userns`, `landlock_sysfs`, `bypass_flag` (`--dangerously-bypass-approvals-and-sandbox`), `use_bypass`, `recommended_sandbox`, `agents_md`, `config_path`, `api_key_present`, `base_url_present`, `full_auto_supported` (always false on this pin).

### codex_exec

| Parameter | Type | Required | Default |
|---|---|---|---|
| prompt | string | yes | |
| model | string | no | empty (Codex default, or `model` in config.toml) |
| cwd | string | no | `WORKSPACE` (`/home/user/workspace`) |
| sandbox | string | no | `auto` |
| approval | string | no | `never` |
| json_events | boolean | no | true |
| resume | string | no | empty. `last` or a session id |
| resume_all | boolean | no | false (`--all`, only with `resume=last`) |
| skip_git_repo_check | boolean | no | true |
| ephemeral | boolean | no | false |
| output_schema | string | no | empty (path to a JSON Schema file) |
| agents_md | string | no | empty (written to `cwd/AGENTS.md` before exec when set) |
| timeout_s | integer | no | 300 (1–3600) |

`sandbox` is `auto`, `bypass`, `read-only`, `workspace-write`, or `danger-full-access`. `approval` is `untrusted`, `on-request`, or `never`.

Returns an object: `thread_id`, `last_message`, `events` (capped at 200), `event_count`, `events_truncated`, `sandbox_requested`, `sandbox_applied`, `bypass`, `argv`, `stderr`.

Argv when the probe succeeds and `sandbox=auto`:

```text
codex exec --color never --json --skip-git-repo-check -C <cwd> --sandbox workspace-write -c approval_policy="never" -- <prompt>
```

Argv when `sandbox=auto` and the probe fails, or `sandbox=bypass`:

```text
codex exec --color never --json --skip-git-repo-check -C <cwd> --dangerously-bypass-approvals-and-sandbox -- <prompt>
```

Resume inserts `resume --last` or `resume <session_id>` before `--`. `--model` is added only when `model` is non-empty. `--full-auto` is not used.

Only `auto` falls back after a failed probe. Explicit `read-only`, `workspace-write`, and `danger-full-access` requests fail before workspace, git, or configuration writes when the sandbox cannot be enforced. Explicit `bypass` remains an operator choice. The result records both the request and the applied mode.

### codex_config_write

| Parameter | Type | Required | Default |
|---|---|---|---|
| base_url | string | no | `ABX_LLM_BASE_URL`, else `OPENAI_BASE_URL` |
| provider | string | no | `compatible` |
| env_key | string | no | first set of `ABX_LLM_API_KEY`, `OPENAI_API_KEY`, `CODEX_API_KEY` |
| model | string | no | `CODEX_MODEL` or `ABX_LLM_MODEL` |
| wire_api | string | no | `responses` (any other value is an error) |
| codex_home | string | no | `CODEX_HOME` or `~/.codex` |

Returns `path`, `provider`, `base_url`, `env_key` (the variable name), `model`, `wire_api`, `supports_websockets` (false), and `toml`. Writes `$CODEX_HOME/config.toml` mode `0600`. Provider ids `openai`, `ollama`, and `lmstudio` are reserved by Codex and rejected. `codex_exec` writes this file only when a base URL is set and the file is absent.

Generated shape:

```toml
model_provider = "compatible"
model = "qwen-plus"

[model_providers.compatible]
name = "OpenAI-compatible"
base_url = "https://example.invalid/v1"
env_key = "ABX_LLM_API_KEY"
wire_api = "responses"
supports_websockets = false
```

`supports_websockets = false` keeps this pin on HTTPS. The default OpenAI provider otherwise opens `wss://api.openai.com/v1/responses`.

### codex_agents_write

| Parameter | Type | Required | Default |
|---|---|---|---|
| content | string | yes | |
| cwd | string | no | `WORKSPACE` |

Returns `path` and `bytes`. Does not call the model.

### codex

| Parameter | Type | Required | Default |
|---|---|---|---|
| prompt | string | yes | |
| model | string | no | empty |

Returns the same object as `codex_exec`. Kept so older clients that called `codex` still have a name. The argv is the exec form above, not `codex -p`.

## How to build

Base image `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>` (`cn-hangzhou`, tag `v0.0.49` unless the CLI overrides them). The image already has Python 3.13 and Node.js 20.

Pins, in `codex/Dockerfile`:

- `npm install -g @openai/codex@0.162.1` (probed with `npm view` on 2026-10-15; `codex --version` prints `codex-cli 0.162.1`).
- `agent-sandbox-server==0.3.0` from python-sdk `61c43e0be65a1f57aa09186d578e7b399e48429b` (includes PR #21). A wheel injected by `abx template deploy` wins; otherwise the Dockerfile installs that git archive (`subdirectory=server-sdk`). The PyPI project named `agent-sandbox` is a different package.

Also installed from apt, unpinned distro packages: `git`, `ripgrep`, `jq`, `ca-certificates`. System `bubblewrap` is not installed, so Codex keeps using the `bwrap` bundled under `codex-resources/` instead of a PATH binary that cannot create user namespaces.

`start_cmd`: `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`

`ready_cmd`: `agent-sandbox-server healthcheck --port 9000`

No `CMD` or `ENTRYPOINT`. Runtime user `user`. `CODEX_HOME=/home/user/.codex`. `WORKSPACE=/home/user/workspace` is a git repo with a starter `AGENTS.md`.

Build context files: `commands.py`, `AGENTS.md`, and an optional `*.whl`.

## Express feasibility

Feasible: yes

Limiting factor: Codex's nested Linux sandbox (bubblewrap user namespaces, seccomp, and the legacy landlock path). Express gives the sandbox user no capabilities, so that inner sandbox often cannot be created. The CLI still runs.

Probed on 2026-10-15 against `@openai/codex@0.162.1`:

- `codex exec --help` has `--json`, `--sandbox read-only|workspace-write|danger-full-access`, `--dangerously-bypass-approvals-and-sandbox`, `-C/--cd`, `--model`, `--skip-git-repo-check`, and `codex exec resume [SESSION_ID]` with `--last`.
- `--full-auto` is an unexpected argument. The survey's `codex exec --full-auto` line is stale for this pin. The non-interactive replacement when the sandbox works is `--sandbox workspace-write` plus `-c approval_policy="never"` (exec has no `--ask-for-approval` flag).
- Docs (developers.openai.com/codex, linux-sandbox README, agent approvals): bubblewrap is the default filesystem sandbox; landlock is an explicit legacy fallback (`features.use_legacy_landlock`) and is not enabled here. In Docker or a container that blocks user namespaces, setuid `bwrap`, or the needed seccomp operations, the documented flags are `--sandbox danger-full-access` or `--dangerously-bypass-approvals-and-sandbox`. The help text for the latter says it is for environments that are already sandboxed. That is Express. The template probes `codex sandbox --permission-profile :read-only -- true` and, on failure, adds the bypass flag.
- On this build VM the probe succeeded (read-only sandbox rejected a write to `/tmp`) and bundled `bwrap --unshare-user` exited 0, with no `/sys/kernel/security/landlock` and with `CapEff` all zero. The same binary inside the built image, as uid 1000, failed the probe: `bwrap: No permissions to create a new namespace`. `codex_setup_check` then set `use_bypass` and `codex_exec` with `sandbox=auto` added `--dangerously-bypass-approvals-and-sandbox`. A prompt `Reply with exactly: ABX_E2E_OK` against an OpenAI-compatible Responses endpoint (`qwen-plus`) returned that marker. Express is the same shape (non-root, no capabilities). The probe is runtime, not a hardcoded bypass, so a host where the sandbox works does not get the flag.

Isolation for an Express run that had to bypass is the platform sandbox, not Codex's bubblewrap. Do not treat the bypass as a substitute for a trusted workspace.

## Risks

- `OPENAI_API_KEY`, `CODEX_API_KEY`, and `ABX_LLM_API_KEY` are empty in `template.yaml` and are injected at create. `config.toml` stores the variable name in `env_key`, never the value. Logs and `RuntimeError` text pass through a redaction of env values whose names contain KEY, SECRET, TOKEN, or PASSWORD.
- `codex exec` reaches the network (the Responses API on the configured `base_url`).
- With the bypass flag, model-generated shell commands are not inside Codex's landlock/bubblewrap/seccomp sandbox. They still run as `user` in the Express container.
- `approval=on-request` can wait until `timeout_s` because exec has no human to answer. The default is `never`.
- This template does not install the standalone `codex-apply-patch` binary and does not serve the Agents API. Those are #60 and #23.
- Unpinned `npm install -g @openai/codex` is intentionally not used.

## Test plan

- L0: `python3 scripts/run_local_e2e.py` (or this directory's `e2e_test.py` against `E2E_BASE_URL`). Expect `/health`, the six command names, HTTP 400 for a missing `prompt`, HTTP 500 `ValueError` for `sandbox=nope` and for `wire_api=chat`, a `codex_setup_check` object whose `bypass_flag` is `--dangerously-bypass-approvals-and-sandbox`, a `config.toml` that contains `wire_api = "responses"` and no key material, and an `AGENTS.md` write. `codex_version` is asserted when `codex` is on PATH and asserted as "not on PATH" when it is not. `E2E_RUN_LLM=0` skips the model case.
- L1: `docker build` of this Dockerfile after substituting the base-image placeholder. The log shows `@openai/codex@0.162.1` and the python-sdk archive `61c43e0be65a1f57aa09186d578e7b399e48429b`.
- L2: `python3 scripts/express_e2e.py codex` on `alicloud-express`. Smoke is `codex_version` expecting `0.162.1`, then `codex_setup_check` (success, no exact body). Both `abx run` and `Sandbox.run`. Evidence only after both pass.
- L3: only with a real authorized key and a Responses-compatible endpoint. The HTTP controller seeds an incorrect existing Fibonacci implementation and two original tests, requires the specific one-failure baseline, and asks the agent to fix the source without changing the original tests. Successful command events and the final marker, a nonempty report, exact acceptance artifact, independent held-out assertions, and reruns of both original and generated tests are required. Empty keys with `E2E_REQUIRE_LLM=1` fail. Independent verifier processes preload standard-library modules with Python `-I`, compile actual source bytes, catch premature exits, require fresh post-agent completion acknowledgements, and reject missing/skipped/expected-failing tests. This ordinary completion guard is not an OS security boundary. This test definition alone establishes no provider acceptance.
- L4: not planned. No e2b, opensandbox, alicloud-container, or cubesandbox credentials will be used.
