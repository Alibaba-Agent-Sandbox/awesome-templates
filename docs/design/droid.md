# Factory Droid

## Purpose

Provide a non-interactive Factory coding agent for projects uploaded through Agent Sandbox. Preserve `droid(prompt)` Factory mode and add genuine native `droid_byok` with an explicit compatible provider, plus both read-only setup inspections. Scope is the CLI, not Factory's hosted workspace or mission orchestration.

## Capabilities

Shell, files, code and ports through the server SDK. `droid` runs a bounded one-shot task; clients retrieve project changes through file APIs and run independent tests through process APIs. This template does not advertise streaming or background execution through a named command.

## Exposed API

- `droid_version() -> str`: `droid --version`; 30-second deadline, no Factory key required.
- `droid_setup_check() -> dict`: installed/package/version/expected_version, key-presence boolean, workspace-existence boolean and disabled-update status; no model call and no secret values.
- `droid(prompt: str, auto: str = "low", cwd: str = "", command_timeout: int = 300) -> str`: prompt is required and nonempty; auto is empty/read-only or low/medium/high; cwd resolves within the existing WORKSPACE, including symlink resolution; deadline is 1–600 seconds. Runs argv `droid exec [--auto LEVEL] -- PROMPT`, buffers stdout, raises sanitized errors on nonzero exit or deadline, and kills the owned process group on timeout.

Compatibility: 1.1.0 changes the project root from `/app` to `/home/user/app` and explicitly defaults to low autonomy so coding can edit files. Passing `auto=""` retains upstream read-only behavior. Public parameters remain JSON scalars; no shell prompt interpolation or unsafe permission bypass is used.

Two additional commands: `droid_byok(prompt: str, cwd: str="", command_timeout: int=300) -> dict`, prompt1–32768 UTF-8 bytes/no NUL; cwd at most4096bytes/existing resolved workspace path; deadline1–600seconds/non-bool. Returns actual native stdout/stderr/exit/version. `droid_byok_setup_check()` returns only explicit model/base/key presence and account-free BYOK mode. Settings are captured at import. BYOK fixed argv uses original `exec --model custom:<configured-model> --output-format json --auto low --disable-builtin-skills --settings <private-settings> --only-tools Read,Edit,Create,Grep,Glob,LS`; task uses anonymous stdin. Full [reference](../../droid/README.md#command-reference).

## How to build

Template1.1.1 explicitly owns /home/user/app as user:user before runtime USER. This repairs actual non-root workspace mkdir/write failures. Earlier provider receipts retain their original source-version scope; this changed profile requires new acceptance.

[Dockerfile](../../droid/Dockerfile) uses Alibaba FC base and immutable servere2cb27e fallback/injected wheel. Full npm0.241.1 lock installs from the official registry with hooks disabled. Execute the fixed Linuxx64 native binary directly; SHA256 is checked at build and every command. Retain [proprietary upstream notice](../../droid/UPSTREAM-NOTICE.md). No public source commit is inferred from package metadata. Rootfs8GiB guard and non-root runtime remain. Version1.2.0 requires fresh image/cloud receipts; historical1.1.1 receipts are unchanged.

Generation 2 starts `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`; ready command is `agent-sandbox-server healthcheck --port 9000`. No image CMD/ENTRYPOINT; runtime user is `user`. [template.yaml](../../droid/template.yaml) declares only empty secret placeholders.

## Express feasibility

Feasible: yes

Limiting factor: none

The headless CLI requires no Docker, KVM or extra capabilities. Target resources are2vCPU/2048MiB with model egress: explicit compatible service for BYOK, Factory for legacy mode. Actual changed-image memory/runtime behavior remains a measured gate; feasibility is not a provider pass.

Both modes use private per-call HOME and identity-pinned group/nonce/pidfd cleanup on success, error, output overflow and timeout. Limit each stream to256KiB. Allowlist the child environment; exclude operator cloud/GitHub credentials. BYOK settings contain only the private endpoint/model and an environment key reference. Only the intended key enters the native process; no Factory key in BYOK. Read [configuration](../../droid/README.md#configuration). BYOK uses native permission low; it does not enable unsafe bypass. Project source/artifacts remain caller-owned.

## Risks

Owned subprocess groups are cleaned after success/nonzero completion as well as timeout. Linux waitid(WNOWAIT) keeps the leader PID reserved through final group KILL; concurrent pipe readers prevent output deadlock, and only then is the leader reaped. Background descendants with redirected stdio cannot survive normal completion.

Factory keys and provider credentials are distinct. Legacy mode requires a Factory key; BYOK requires only its explicit compatible settings. Setup does not log in or invoke a model. Auto-update is disabled. Legacy retains its argv contract; BYOK task stdin is an anonymous memory file. Redact raw/JSON-escaped key/base values, preserve native exits and remove owned private state. Marked detached descendants are identified with nonce plus pidfd; unrelated processes are preserved. Explicit legacy medium/high autonomy remains a caller choice; BYOK is fixed low. Project files require normal secret hygiene; cwd is not an OS security boundary.

## Test plan

- Regression: `python3 -m pytest -q droid/test_commands.py droid/test_e2e_protocol.py droid/test_byok.py droid/test_model_controller.py`; authored process, bound, secret isolation, cleanup, genuine terminal-result and independent verifier contracts. Mocks do not qualify the native product.
- L0: source-only HTTP may explicitly SKIP missing native version when CLI is not required. This never establishes native/Express acceptance. Actual-image and Express controllers require the installed fixed binary and refuse skips.
- L1: build image and verify exact `0.241.1` in the Docker install assertion; unavailable without Docker.
- L2: `python3 scripts/express_e2e.py droid`; `droid_version` must equal `0.241.1` through external CLI and SDK before provider evidence may be listed.
- L3: `E2E_RUN_LLM=1 E2E_REQUIRE_LLM=1 E2E_REMOTE_SANDBOX=1` with the explicit approved compatible settings on a fresh cloud target. Actual SDK command, genuine positive-turn terminal JSON and exact fresh final response; existing source edit, new artifacts, byte-identical original tests, complete original and held-out checks with unpredictable post-return ACKs and independently confirmed owned project absence. Missing model keys/skipped native checks fail. Legacy Factory model controller remains separate and requires that account key.
- L4: no other-provider run planned or claimed in this change.

Refs [Droid issue #19](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/19) and [official Droid Exec documentation](https://docs.factory.com/droid-exec/overview).

Current1.2 qualification plan: preserved legacy tests plus BYOK validation/process/controller tests; exact native synthetic-only wire probe before real credentials; actual L1; SDK-created canonical steps with full HTTP and official READY; actual approved-model source edit, fresh report/nonce artifact, byte-identical original tests, complete independent original+held-out post-return checks and owned cleanup. A marker alone cannot certify native completion. Current Factory-account model mode remains unverified. [Decision](../../.agents/notes/proposed/feature/2026-10-20-droid-explicit-byok.md).

Pinned `--settings` supplies the private runtime-priority model settings. Restrict native tools to Read/Edit/Create/Grep/Glob/LS; independent post-return cloud checks execute the original and held-out tests. No native Execute, subagent or MCP tools are enabled for BYOK.

Native cwd is a private temporary Git root, while validated `cwd` selects the project communicated through anonymous stdin for absolute native file-tool paths. This avoids project custom-model configuration collisions; no target-project native settings are loaded automatically.
