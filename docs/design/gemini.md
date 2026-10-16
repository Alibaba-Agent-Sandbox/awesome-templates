# gemini

## Purpose

Expose Gemini CLI for project inspection and explicitly authorized coding through the named-command HTTP contract. Refs [Issue #30](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/30).

## Capabilities

Headless CLI calls, read-only installation/setup diagnostics, files and process APIs on port 9000. The command defaults to upstream plan mode; tool edits/shell need explicit `yolo=true`. Starting directories must resolve inside WORKSPACE. The runtime provides isolation; this is not a tool filesystem sandbox.

## Exposed API

`gemini(prompt: str, model: str="", cwd: str="", command_timeout: int=600, yolo: bool=False) -> str`. Prompt is required/nonempty; timeout is 1–1800 seconds. Model resolves argument, GEMINI_MODEL, then gemini-3.1-flash-lite. cwd resolves inside WORKSPACE. argv is `gemini -p <prompt> --model <model> --output-format json --approval-mode plan|yolo`. No shell interpolation; stdin DEVNULL; process-group deadline kills descendants. Both success/failure output redact secret environment values.

`gemini_version() -> str` runs `gemini --version`, deadline 30 seconds. `gemini_setup_check() -> dict` reports installation, pin/version, key-presence boolean, model-presence/workspace and settings metadata. It never creates or rewrites config or returns configuration contents. Existing OAuth/Vertex settings remain user-owned. HTTP arguments are typed from signatures; execution errors are HTTP 500.

## How to build

[Dockerfile](../../gemini/Dockerfile) uses Alibaba runtime base (default v0.0.49 region cn-hangzhou, resolved by deploy), exact `@google/gemini-cli@0.64.0`, and server archive pin `35da216a300f1e2e84254a1cf4b4a7ea98681505` or an injected build wheel. Actual package metadata says Node >=20; local actual binary/help verified version and supported flags. Uses base Node instead of another unpinned Node installer. Workdir /home/user/app, user user, generation 2, start `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`, readiness `agent-sandbox-server healthcheck --port 9000`. No CMD/ENTRYPOINT. npm cache is removed in the install layer.

## Express feasibility

Feasible: yes

Limiting factor: real Gemini API key and model availability for L3; no image/cloud acceptance in the current runtime without Docker.

The whole headless CLI fits the stated 2 vCPU/4096 MB non-root runtime without KVM, Docker or privileged capabilities. That feasibility analysis does not establish a provider pass.

## Risks

Owned subprocess groups are cleaned after success/nonzero completion as well as timeout. Linux waitid(WNOWAIT) keeps the leader PID reserved through final group KILL; concurrent pipe readers prevent output deadlock, and only then is the leader reaped. Background descendants with redirected stdio cannot survive normal completion.

Prompts and tools make external model/network calls. yolo approves edits and shell inside the sandbox and must be explicit. No missing-key OAuth fallback. Model availability varies by key. Settings are inspected without mutation; malformed JSON is reported, not repaired. Existing upstream settings/extensions remain relevant. Logs and public records must never contain credentials. The wrapper redacts credential-valued environment variables, including JSON-escaped values, and strips timeout exception chains that would include prompt argv. Client HTTP timeout is independent from process deadline.

## Test plan

L0: checker, behavior regressions, actual local server HTTP contract via run_local_e2e with model forced off. Regressions cover argv/permission flags, missing-key no spawn, setup preserving config/mode, cwd symlinks/traversal, output redaction, timeout descendant cleanup, target-key detection, zero forced-off coding requests and rejected false L3 passes.

L1: real Docker build and visible 0.64.0 version, unavailable when Docker is missing. L2: deploy with unique task alias, external CLI and SDK smoke gemini_version==0.64.0; remove owned resources. L3: target setup must report Gemini key; controller keys are irrelevant. Through remote files/process APIs, seed a failing calculator, require fixing existing source, preserving tests and creating REPORT.md plus exact randomized ABX_E2E_OK artifact, rerun tests independently and held-out arithmetic, clean unique project. Marker-only answers fail. E2E_REQUIRE_LLM makes missing key or forced-off model execution fail. No L4 provider is claimed.
