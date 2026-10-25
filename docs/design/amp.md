# amp

## Purpose

Operators who want Sourcegraph Amp's coding CLI inside an Agent Sandbox. The sandbox installs a pinned `@ampcode/cli` and exposes non-interactive commands. A live `amp -x` turn needs Amp's own access token (`AMP_API_KEY`). DashScope and other OpenAI-compatible keys are not accepted.

## Capabilities

After READY the sandbox has the `amp` binary, git, and ripgrep, and it serves named commands on port 9000.

The Express slice that does not need a key is `amp_version` and `amp_setup_check` (install probe, settings file, key-present boolean). `amp_execute` is the live execute-mode call. It is not part of the keyless smoke.

Amp can edit files and run shell tools inside the sandbox once a real key is present. This template does not start a TUI, an orb, or a desktop.

## Exposed API

`amp_version`

- Parameters: none.
- Returns: string, the first token of `amp version` (the npm version, not the "released … ago" suffix).
- Upstream argv: `amp version`.
- No `AMP_API_KEY`. A missing binary raises `RuntimeError`.

`amp_setup_check`

- Parameters: none.
- Returns: object with `installed` (bool), `package` (`@ampcode/cli`), `version` (string, empty when the binary is missing), `api_key_set` (bool, never the secret), `settings_path` (string), `dangerously_allow_all` (bool), `updates_mode` (string), `settings_exists` (bool).
- Upstream argv: `amp version` when the binary is on `PATH`. The command reads the existing settings file without creating or modifying it. It does not call `amp -x`.
- Image default settings JSON at `AMP_SETTINGS_FILE`, or `$HOME/.config/amp/settings.json`, or `$WORKSPACE/.e2e_amp/settings.json` when `WORKSPACE` is set and `AMP_SETTINGS_FILE` is not:
  - `amp.dangerouslyAllowAll`: false
  - `amp.updates.mode`: `disabled`
  - `amp.notifications.enabled`: false

`amp_execute`

- Parameters: `prompt` (string, required), `stream_json` (bool, optional, default false), `dangerously_allow_all` (bool, optional, default false).
- Returns: string, the full stdout after the process exits. With `stream_json` true that stdout is the JSONL from `--stream-json`, not an HTTP stream.
- Upstream argv: `amp --no-color --no-notifications --no-ide -x <prompt>`, plus `--stream-json` when requested and `--dangerously-allow-all` only with the explicit permission option. The prompt is one argv element.
- Requires a non-empty `AMP_API_KEY`. If it is missing the function raises `RuntimeError` and does not start the CLI. The CLI itself, without this guard, prints a device-login URL and waits.

Probed on 2026-10-15 from `@ampcode/cli@0.0.1792022479-ge66e24` (`amp --help`, `amp version`, and a no-key `amp -x`). `-x` / `--execute` and `--stream-json` are documented options. `--dangerously-allow-all` is not listed in that `--help` options section. The binary's own error strings tell the user to rerun with it, and a call that includes the flag is not rejected as an unknown option. The documented settings key for the same behavior is `amp.dangerouslyAllowAll`. The command passes the flag only with an explicit dangerously_allow_all=true request and never rewrites the settings.

## How to build

Base image `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>` (`cn-hangzhou`, `v0.0.49` unless the CLI overrides them). No `CMD` or `ENTRYPOINT`.

`generation: 2`

`start_cmd`: `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`

`ready_cmd`: `agent-sandbox-server healthcheck --port 9000`

Pins in the Dockerfile:

- `@ampcode/cli@0.0.1792022479-ge66e24` (`npm view @ampcode/cli version` on 2026-10-15), installed with `--registry https://registry.npmjs.org`. The base image's npm registry is `registry.npmmirror.com`, which 404s `@ampcode/cli-linux-x64` at this version; without the official registry the wrapper installs and `amp` is a stub. The optional dependency `@ampcode/cli-linux-x64` is the same version. The previous directory pin `0.0.1791964847-g13f24a` still exists and is older.
Install the exact published `agent-sandbox-server==0.4.0a4` distribution from PyPI, as declared in the Dockerfile.

The image sets `AMP_SETTINGS_FILE=/home/user/.config/amp/settings.json` and `AMP_LOG_FILE=/home/user/.cache/amp/logs/cli.log`. Node.js 20 from the base image is only used to run `npm`. The `amp` executable is a glibc ELF.

## Express feasibility

Feasible: yes

Limiting factor: none

Express (non-root `user`, 2 vCPU, no KVM, no Docker, no extra capabilities, about 10G rootfs, egress allowed) can run this CLI. `amp version` does not need a key or a TUI. A live execute-mode turn needs outbound HTTPS to `https://ampcode.com/` and `AMP_API_KEY`. That key is an account requirement, not a platform limit. The image does not use `/dev/kvm`, Docker, or a replaced entrypoint.

## Risks

Owned subprocess groups are cleaned after success/nonzero completion as well as timeout. Linux waitid(WNOWAIT) keeps the leader PID reserved through final group KILL; concurrent pipe readers prevent output deadlock, and only then is the leader reaped. Background descendants with redirected stdio cannot survive normal completion.

- `AMP_API_KEY` is an Amp access token from https://ampcode.com/settings/security#access-token. `ABX_LLM_API_KEY`, DashScope, OpenAI, and Anthropic keys do not authenticate this CLI. The template never reads those variables.
- Without the guard in `amp_execute`, `amp -x` with no key starts a device login and blocks. The named command returns an error instead.
- An explicit `dangerously_allow_all=true` request (or caller-owned settings with `amp.dangerouslyAllowAll: true`) lets the agent run tools without a prompt. The sandbox boundary is the containment. Do not point this at a host checkout.
- Settings disable Amp's auto-update (`amp.updates.mode: disabled`) so a running sandbox does not replace the pinned binary.
- The command returns process stdout in one response. It does not proxy `--stream-json` as a live HTTP stream.
- Logs and `RuntimeError` text have `AMP_API_KEY` redacted when the value is non-empty. `api_key_set` is only a boolean.

## Test plan

L0: `python3 scripts/run_local_e2e.py` (or `e2e_test.py` against `E2E_BASE_URL`). Expect `/health`, the four command names, HTTP 400 when `prompt` is missing, HTTP 500 mentioning `AMP_API_KEY` when the key is empty (and no device-login URL), `amp_setup_check` preserving existing settings and reporting missing settings without creating files, and `amp_version` returning `0.0.1792022479-ge66e24` when `amp` is on `PATH` or a not-found error when it is not. `E2E_RUN_LLM=0` skips the live execute call.

L1: `docker build` log contains `0.0.1792022479-ge66e24` from `amp version` and the server package version declared in the Dockerfile.

L2: `template.yaml` smoke is `amp_version` expecting `0.0.1792022479-ge66e24`, and `amp_setup_check` expecting `installed: true`, `api_key_set: false`, settings path `/home/user/.config/amp/settings.json`, `settings_exists: true`, `dangerously_allow_all: false`, `updates_mode: disabled`. `scripts/express_e2e.py amp` runs both through `abx run` and `Sandbox.run`.

L3: only when `AMP_API_KEY` is set in the environment that starts the server. The verifier creates a unique target project, proves its seeded source fails three tests, and invokes `amp_execute` with explicit tool approval to repair the source and create report/acceptance artifacts. It downloads the changed source, unchanged tests and new artifacts through the target files API, then independently reruns isolated Python tests and held-out calculations through the target process API. Writable startup hooks or standard-library shadows cannot replace the verifier. The owned project is deleted in `finally`. A response marker alone cannot pass. Set `E2E_WORKSPACE` to the target workspace when it differs from `/home/user/app`. This environment has no `AMP_API_KEY`; do not substitute DashScope. L3 stays unverified.

L4: not planned. No other provider will be claimed.

Ran on 2026-10-15: L0 and L1 passed. L2 on alicloud-express passed for `amp_version` and `amp_setup_check` through `abx run` and `Sandbox.run` (template version 1.1.0, SDK 0.3.0). L3 was not run. `abx template deploy` logged a PyPI 404 for `agent-sandbox-server==0.3.0` and then used the Dockerfile archive pin. That warning is [agent-sandbox#24](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues/24).

Version 1.2.0 acceptance remains incomplete. The 2026-10-15 L1/L2 result above applies only to 1.1.0. Its evidence is preserved; the 1.2.0 catalog remains experimental and tested_on is empty. No authorized AMP_API_KEY is available for the required real coding/model task.
