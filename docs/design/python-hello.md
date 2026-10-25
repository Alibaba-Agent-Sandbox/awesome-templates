# python-hello

## Purpose

Provide a small, understandable Python development sandbox for users learning the command server or uploading Python source and tests. It is maintained in this repository rather than wrapping an upstream agent.

## Capabilities

Expose greetings, inline Python, uploaded scripts, pytest, one hidden debug command, a custom HTTP GET route, and the built-in shell/files/ports APIs. The full template fits Express without a model key.

## Exposed API

| Command | Parameters | Return | Upstream argv |
|---|---|---|---|
| `hello` | `name: str`, optional, `World` | greeting string | None |
| `run_script` | `code: str`, required | stdout string | `[sys.executable, '-c', code]`, 30-second deadline |
| `run` | `file: str`, optional, `main.py` | stdout string | `[sys.executable, file]`, 60-second deadline |
| `test` | `path: str`, optional, `.` | stdout string | `[sys.executable, '-m', 'pytest', '-p', 'no:cacheprovider', path]`, 120-second deadline |
| `_debug_info` | None, hidden | Python/system object | None |

`GET /hello/{name}` returns a greeting object. Named commands use `POST /commands/<name>` with direct JSON arguments and return `{"result": ...}`. All Python subprocesses use `WORKSPACE`, or the directory containing `commands.py`; missing workspaces fail rather than falling back elsewhere.

## How to build

Template1.1.1 explicitly owns /home/user/app as user:user before runtime USER. This repairs actual non-root workspace mkdir/write failures. Earlier provider receipts retain their original source-version scope; this changed profile requires new acceptance.

The [Dockerfile](../../python-hello/Dockerfile) uses Alibaba base placeholders resolved by `abx` (default `cn-hangzhou`, `v0.0.49`), the published server package pinned in the Dockerfile, and `pytest==8.4.2`. Runtime is non-root `user` at `/home/user/app`. Generation-2 start command is `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`; ready command is `agent-sandbox-server healthcheck --port 9000`. No CMD/ENTRYPOINT overrides the platform entrypoint.

## Express feasibility

Feasible: yes

Limiting factor: none

The complete template runs within non-root `user`, 2 vCPU, no KVM/Docker/extra capabilities and approximately 10G rootfs. Python/pytest need no model service or outbound network after image creation.

## Risks

Commands intentionally run caller-provided Python, including filesystem and network access; optional bearer authentication and provider isolation govern access. The file API boundary does not sandbox arbitrary Python. No secrets are baked into the image. Script/test failures, startup failures and deadlines return fixed errors, with exit codes when available. Captured error output and argv/source code are omitted; successful stdout is returned explicitly. `python3 -m pytest python-hello/test_command_errors.py -q` regresses these cases with synthetic secret markers and actual subprocesses. Fixed command deadlines are separate from HTTP client timeouts; background workloads need the process API. Version 1.0.0 historical hello-only Express evidence is preserved; it does not validate 1.1.0.

## Test plan

- L0: `python3 scripts/run_local_e2e.py` starts a real local server. Assert command discovery/hiding, greeting/custom route, inline code, argument/unknown-command errors, file upload/download/list/delete, uploaded script output `42`, passing pytest, failing pytest as HTTP 500, shell response, and cleanup. No file-operation SKIP is accepted.
- L1: build the Dockerfile, verify the declared installed server package version and `pytest==8.4.2`, check `USER user`, and invoke `run`/`test` in the image. Requires Docker; no local HTTP result substitutes for this.
- L2: `python scripts/public_launch_e2e.py python-hello --provider alicloud-express --application-controller --source ./python-hello --output python-hello-attempt-1.json` deploys READY, creates a sandbox, calls `hello` and `run_script` through CLI and SDK and asserts `Hello, Express!`/`42`. Only then retain new provider evidence for the actual template version.
- Product workflow: run `e2e_test.py` against the remote port URL with `E2E_WORKSPACE=/home/user/app` so file/script/pytest behavior is checked remotely as well. This is distinct from harness smoke coverage.
- L3 model calls do not apply: this template is Python tooling, not a model-powered agent. L4 providers remain unverified until independently run.
