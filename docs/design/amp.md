# amp

## Purpose

Operators who want Sourcegraph Amp's coding CLI inside an Agent Sandbox. The sandbox installs a pinned `@ampcode/cli` and exposes non-interactive commands. A live `amp -x` turn needs Amp's own access token (`AMP_API_KEY`). DashScope and other OpenAI-compatible keys are not accepted.

## Capabilities

After READY the sandbox has the `amp` binary, git, and ripgrep, and it serves named commands on port 9000.

The Express slice that does not need a key is `amp_version` and `amp_setup_check` (install probe, settings file, key-present boolean). `amp_execute` is the live execute-mode call. It is not part of the keyless smoke. The previous command name `amp` remains as an alias of `amp_execute`.

Amp can edit files and run shell tools inside the sandbox once a real key is present. This template does not start a TUI, an orb, or a desktop.

## Exposed API

`amp_version`

- Parameters: none.
- Returns: string, the first token of `amp version` (the npm version, not the "released … ago" suffix).
- Upstream argv: `amp version`.
- No `AMP_API_KEY`. A missing binary raises `RuntimeError`.

`amp_setup_check`

- Parameters: none.
- Returns: object with `installed` (bool), `package` (`@ampcode/cli`), `version` (string, empty when the binary is missing), `api_key_set` (bool, never the secret), `settings_path` (string), `dangerously_allow_all` (bool), `updates_mode` (string).
- Upstream argv: `amp version` when the binary is on `PATH`. The command also writes the settings file below. It does not call `amp -x`.
- Settings JSON (created or updated) at `AMP_SETTINGS_FILE`, or `$HOME/.config/amp/settings.json`, or `$WORKSPACE/.e2e_amp/settings.json` when `WORKSPACE` is set and `AMP_SETTINGS_FILE` is not:
  - `amp.dangerouslyAllowAll`: true
  - `amp.updates.mode`: `disabled`
  - `amp.notifications.enabled`: false

`amp_execute`

- Parameters: `prompt` (string, required), `stream_json` (bool, optional, default false).
- Returns: string, the full stdout after the process exits. With `stream_json` true that stdout is the JSONL from `--stream-json`, not an HTTP stream.
- Upstream argv: `amp --dangerously-allow-all --no-color --no-notifications --no-ide -x <prompt>`, plus `--stream-json` when requested. The prompt is one argv element.
- Requires a non-empty `AMP_API_KEY`. If it is missing the function raises `RuntimeError` and does not start the CLI. The CLI itself, without this guard, prints a device-login URL and waits.

`amp`

- Same parameters and return as `amp_execute`. Kept so callers of the previous command name still work.

Probed on 2026-10-15 from `@ampcode/cli@0.0.1792022479-ge66e24` (`amp --help`, `amp version`, and a no-key `amp -x`). `-x` / `--execute` and `--stream-json` are documented options. `--dangerously-allow-all` is not listed in that `--help` options section. The binary's own error strings tell the user to rerun with it, and a call that includes the flag is not rejected as an unknown option. The documented settings key for the same behavior is `amp.dangerouslyAllowAll`. The command sets both.

## How to build

Base image `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>` (`cn-hangzhou`, `v0.0.49` unless the CLI overrides them). No `CMD` or `ENTRYPOINT`.

`generation: 2`

`start_cmd`: `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`

`ready_cmd`: `agent-sandbox-server healthcheck --port 9000`

Pins in the Dockerfile:

- `@ampcode/cli@0.0.1792022479-ge66e24` (`npm view @ampcode/cli version` on 2026-10-15), installed with `--registry https://registry.npmjs.org`. The base image's npm registry is `registry.npmmirror.com`, which 404s `@ampcode/cli-linux-x64` at this version; without the official registry the wrapper installs and `amp` is a stub. The optional dependency `@ampcode/cli-linux-x64` is the same version. The previous directory pin `0.0.1791964847-g13f24a` still exists and is older.
- `agent-sandbox-server` from `https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/61c43e0be65a1f57aa09186d578e7b399e48429b.tar.gz#subdirectory=server-sdk`. That commit is python-sdk `main` and is PR #21. The distribution is not on PyPI.

The image sets `AMP_SETTINGS_FILE=/home/user/.config/amp/settings.json` and `AMP_LOG_FILE=/home/user/.cache/amp/logs/cli.log`. Node.js 20 from the base image is only used to run `npm`. The `amp` executable is a glibc ELF.

## Express feasibility

Feasible: yes

Limiting factor: none

Express (non-root `user`, 2 vCPU, no KVM, no Docker, no extra capabilities, about 10G rootfs, egress allowed) can run this CLI. `amp version` does not need a key or a TUI. A live execute-mode turn needs outbound HTTPS to `https://ampcode.com/` and `AMP_API_KEY`. That key is an account requirement, not a platform limit. The image does not use `/dev/kvm`, Docker, or a replaced entrypoint.

## Risks

- `AMP_API_KEY` is an Amp access token from https://ampcode.com/settings/security#access-token. `ABX_LLM_API_KEY`, DashScope, OpenAI, and Anthropic keys do not authenticate this CLI. The template never reads those variables.
- Without the guard in `amp_execute`, `amp -x` with no key starts a device login and blocks. The named command returns an error instead.
- `--dangerously-allow-all` plus `amp.dangerouslyAllowAll: true` lets the agent run tools without a prompt. The sandbox boundary is the containment. Do not point this at a host checkout.
- Settings disable Amp's auto-update (`amp.updates.mode: disabled`) so a running sandbox does not replace the pinned binary.
- The command returns process stdout in one response. It does not proxy `--stream-json` as a live HTTP stream.
- Logs and `RuntimeError` text have `AMP_API_KEY` redacted when the value is non-empty. `api_key_set` is only a boolean.

## Test plan

L0: `python3 scripts/run_local_e2e.py` (or `e2e_test.py` against `E2E_BASE_URL`). Expect `/health`, the four command names, HTTP 400 when `prompt` is missing, HTTP 500 mentioning `AMP_API_KEY` when the key is empty (and no device-login URL), `amp_setup_check` writing settings, and `amp_version` returning `0.0.1792022479-ge66e24` when `amp` is on `PATH` or a not-found error when it is not. `E2E_RUN_LLM=0` skips the live execute call.

L1: `docker build` log contains `0.0.1792022479-ge66e24` from `amp version` and the python-sdk archive commit `61c43e0be65a1f57aa09186d578e7b399e48429b`.

L2: `template.yaml` smoke is `amp_version` expecting `0.0.1792022479-ge66e24`, and `amp_setup_check` expecting `installed: true`, `api_key_set: false`, settings path `/home/user/.config/amp/settings.json`, `dangerously_allow_all: true`, `updates_mode: disabled`. `scripts/express_e2e.py amp` runs both through `abx run` and `Sandbox.run`.

L3: only when `AMP_API_KEY` is set in the environment that starts the server. Prompt `Reply with exactly: ABX_E2E_OK` via `amp_execute`. This environment has no `AMP_API_KEY`. Do not substitute DashScope. L3 stays unverified.

L4: not planned. No other provider will be claimed.

Ran on 2026-10-15: L0 and L1 passed. L2 on alicloud-express passed for `amp_version` and `amp_setup_check` through `abx run` and `Sandbox.run` (template version 1.1.0, SDK 0.3.0). L3 was not run. `abx template deploy` logged a PyPI 404 for `agent-sandbox-server==0.3.0` and then used the Dockerfile archive pin. That warning is [agent-sandbox#24](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues/24).
