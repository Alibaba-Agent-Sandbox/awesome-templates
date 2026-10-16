# Factory Droid

## Purpose

Provide a non-interactive Factory coding agent for projects uploaded through Agent Sandbox. Preserve the existing `droid(prompt)` command and add actual installation inspection without a model call. Scope is the CLI, not Factory's hosted workspace or mission orchestration.

## Capabilities

Shell, files, code and ports through the server SDK. `droid` runs a bounded one-shot task; clients retrieve project changes through file APIs and run independent tests through process APIs. This template does not advertise streaming or background execution through a named command.

## Exposed API

- `droid_version() -> str`: `droid --version`; 30-second deadline, no Factory key required.
- `droid_setup_check() -> dict`: installed/package/version/expected_version, key-presence boolean, workspace-existence boolean and disabled-update status; no model call and no secret values.
- `droid(prompt: str, auto: str = "low", cwd: str = "", command_timeout: int = 300) -> str`: prompt is required and nonempty; auto is empty/read-only or low/medium/high; cwd resolves within the existing WORKSPACE, including symlink resolution; deadline is 1–600 seconds. Runs argv `droid exec [--auto LEVEL] -- PROMPT`, buffers stdout, raises sanitized errors on nonzero exit or deadline, and kills the owned process group on timeout.

Compatibility: 1.1.0 changes the project root from `/app` to `/home/user/app` and explicitly defaults to low autonomy so coding can edit files. Passing `auto=""` retains upstream read-only behavior. Public parameters remain JSON scalars; no shell prompt interpolation or unsafe permission bypass is used.

## How to build

[Dockerfile](../../droid/Dockerfile) uses the Alibaba platform base, bundled Node >=20 and Python, exact npm `@factory/cli@0.241.1`, and the exact python-sdk archive `61c43e0be65a1f57aa09186d578e7b399e48429b` for server SDK fallback. BuildKit accepts the optional injected wheel copy. The installer uses the official npm registry with optional platform packages included and asserts the actual CLI version. The base mirror returned 404 for @factory/cli-linux-x64@0.241.1, causing an upstream fallback to create a self-referencing bin/droid link in the first actual image-build run. npm metadata and the locally installed binary confirmed that pin on 2026-10-16; no blind upstream upgrade was made.

Generation 2 starts `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`; ready command is `agent-sandbox-server healthcheck --port 9000`. No image CMD/ENTRYPOINT; runtime user is `user`. [template.yaml](../../droid/template.yaml) declares only empty secret placeholders.

## Express feasibility

Feasible: yes

Limiting factor: none

The headless CLI requires no Docker, KVM or extra capabilities. Defaults fit the platform's 2 vCPU/2048 MB configuration and use network egress for Factory. This feasibility analysis is not a passing Express deployment record. L1/L2 remain required.

## Risks

Owned subprocess groups are cleaned after success/nonzero completion as well as timeout. Linux waitid(WNOWAIT) keeps the leader PID reserved through final group KILL; concurrent pipe readers prevent output deadlock, and only then is the leader reaped. Background descendants with redirected stdio cannot survive normal completion.

The Factory key is distinct from provider keys. A missing Factory key fails before launching the CLI; setup checks never log in or invoke a model. The subprocess disables auto-update, closes stdin and uses its own process group. Errors omit the original timeout exception and argv; stdout/error redaction covers raw and JSON-escaped configured secret values. Agent-created files require normal secret management. Cwd validation is not an OS isolation boundary. Explicit medium/high autonomy can run more powerful operations; low is the default and read-only is available. A detached descendant outside the owned group cannot be cancelled by this wrapper; use process APIs for managed background work.

## Test plan

- Regression: `python3 -m pytest -q droid/test_commands.py droid/test_e2e_protocol.py`; real subprocess tests cover success/error secret filtering, argv handling, workspace ownership and process-tree deadline cleanup. Mock protocol tests prove remote key authority and reject marker-only false positives.
- L0: `python3 scripts/run_local_e2e.py` with the actual pinned Droid available on PATH. HTTP checks validate signatures, malformed requests, version, setup and missing-key guard; model acceptance stays not run when disabled. No fake CLI or missing-version skip is allowed.
- L1: build image and verify exact `0.241.1` in the Docker install assertion; unavailable without Docker.
- L2: `python3 scripts/express_e2e.py droid`; `droid_version` must equal `0.241.1` through external CLI and SDK before provider evidence may be listed.
- L3: `E2E_RUN_LLM=1 E2E_REQUIRE_LLM=1` with a real target Factory key. Upload buggy calc.py and fixed tests, reproduce baseline failures, request source edits plus a report and acceptance marker, download target files, prove tests preserved, rerun fixed and held-out tests independently with a clean environment, and delete only the owned project. A marker alone fails; missing keys fail required acceptance.
- L4: no other-provider run planned or claimed in this change.

Refs [Droid issue #19](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/19) and [official Droid Exec documentation](https://docs.factory.com/droid-exec/overview).
