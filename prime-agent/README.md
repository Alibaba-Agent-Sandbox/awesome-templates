# prime-agent

## What it does

Runs the unchanged stable Prime Agent0.10.0 native Rust CLI with its original CPython REPL tool named `ipython`. Uses an explicitly approved compatible model and supported fixed kernel interpreter. This bounded headless coding slice does not qualify daemon sessions, recursive agents, subscription models or research benchmarks. [official release](https://github.com/PrimeIntellect-ai/prime-agent/releases/tag/v0.10.0); [pinned native source](https://github.com/PrimeIntellect-ai/prime-agent/tree/763094e1b6a7c17450ee8399b06cda1853847ca5).

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a2`, installed directly by the Dockerfile.

Alibaba generation2 basev0.0.49/Python3.13/Linuxx64; original release archive and executable verified against official manifest SHA256s. Full original sidecars/runtime source0.1.0/protocol3 and licenses retained. Isolated49-package Python hash lock; native supported fixed interpreter skips floating uv/bootstrap. Server source e2cb27e24fde0a67112f82b8d44af463445a5d1a, non-root user, port9000. [Dockerfile](Dockerfile), [provenance](upstream.json), [lock](requirements.lock), [design](../docs/design/prime-agent.md).

## Problem solved

Expose actual native coding through Agent Sandbox without interactive account login, shared developer configuration or operator-side generated-code execution. Native provider resolution, CPython protocol, terminal events and owned cleanup are checked separately; installation/version output alone does not establish coding success.

## Quick start (CLI)

Follow the [usage guide](../docs/using-templates.md#installation) to install the clients, configure the provider and set an independent `ABX_SERVER_TOKEN`. From this repository's root, launch the application and retain its sandbox ID. Replace `<sandbox-id>` below with that ID.

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./prime-agent --yes
abx run <sandbox-id> prime_agent_version --json-args '{}'
```

`template launch` prepares and starts this instance's application. For OpenSandbox, set `ABX_PROVIDER=opensandbox` above and use `provider="opensandbox"` in Python. See the [complete calling flow](../docs/using-templates.md#cli-sdk-and-http) for OpenSandbox configuration, provider selection on every call and owned-resource cleanup. The next examples reuse the same running instance.

## Quick start (Python SDK)

Install `agent-sandbox-client` and follow the [Python connection example](../docs/using-templates.md#cli-sdk-and-http), using `ProviderSandbox.connect` and `application_client` with the independent application token. Replace the command call inside that example's `try` block with:

```python
print(await client.commands.run('prime_agent_version'))
```

Keep the guide's connection and close steps. `sb.commands.run` executes a process; `client.commands.run` calls this template's named commands. Business commands, arguments and limits are listed in the command reference below.

## Quick start (HTTP POST)

Follow the [HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserve gateway headers, path and query parameters, and set the independent application token. Change the request to `POST /commands/prime_agent_version`, with `Content-Type: application/json` and this direct argument object:

```json
{}
```

Expected response for this check:

```json
{"result": {"native_version": "0.10.0"}}
```

`result` is buffered, not an event stream. Missing or mistyped arguments return 400, failed authentication 401, unknown commands 404, and execution errors 500. Set the HTTP wait and command deadline separately; a client timeout does not guarantee cancellation.

## Command reference

| Command | Parameters | Result / effects |
| --- | --- | --- |
| prime_agent_version | none | Actual checked binary/version: `{native_version:"0.10.0"}`; no model |
| prime_agent_kernel_check | none | Original CPython runtime protocol3,12 required imports: `{protocol_version:3,required_imports_checked:12}`; no model or bootstrap |
| prime_agent_setup_check | none | mode `original-native-prime-cpython-repl`; subscription_required:false; api_key_set/base_url_set/model_set booleans; read-only |
| prime_agent | prompt: required nonempty string1..32768UTF-8 bytes/no NUL; cwd: optional string default empty, max4096bytes, existing directory resolved inside WORKSPACE; command_timeout: integer1..600seconds default300 | `{stdout:string,stderr:string,exit_code:int,native_version:"0.10.0",native_completed:bool}`; real original native tools may modify files |

Fixed flags: --offline --mode json --provider abx-approved --model <configured-model> --thinking off --no-session --no-skills --no-prompt-templates --no-themes --no-context-files --cwd <private-git-root> --print. Prompt enters anonymous stdin with the absolute selected project path. The actual native cwd is a private Git root so caller project settings cannot replace the explicit provider. Native `ipython` executes original CPython code. Tool processes have the disposable sandbox user's OS permissions; the cwd guard is not an additional OS sandbox.

Transparent event filtering preserves original settled NDJSON records unchanged and discards incremental update duplicates: raw stdout16MiB, line1MiB, retained stdout256KiB, stderr256KiB. Native exit status/signals are retained. native_completed requires exit0, native turn_end/agent_end and final assistant stopReason=stop. Coding acceptance additionally requires a successful original ipython tool result and independent original/held-out tests. Calls serialize; overlap fails busy. Deadline/overflow/failure cleans the owned process group, nonce-identified descendants and private HOME/config/cache/kernel state.

## Configuration

| Name | Default / requirement | Meaning |
| --- | --- | --- |
| PRIME_MODEL_API_KEY | empty; required for coding | Approved compatible-model key |
| PRIME_MODEL_BASE_URL | empty; required for coding | Explicit HTTPS base; literal local HTTP for authored fixtures only; no userinfo/query/fragment; max2048characters |
| PRIME_MODEL | empty; required for coding | Actual model identifier; max200allowed identifier characters |
| WORKSPACE | `/home/user/workspace` | Existing caller project root |
| ABX_SERVER_TOKEN | required; empty declaration | Export an independent application token before the template launch; separate from model and gateway credentials |

Captured when commands.py loads. Private0700HOME/0600models.json uses apiKey="ABX_PRIME_MODEL_KEY", storing an environment reference instead of key bytes. No operator cloud/GitHub/vendor credentials are inherited. The fixed kernel launcher removes ABX_PRIME_MODEL_KEY before original CPython starts; same-user OS access means this is environment minimization, not credential isolation. Literal/JSON-escaped key and base values are redacted from returned output. Telemetry/traces/refinement/compaction/factory and discovery are disabled; rlmMaxDepth0 is set. Original print mode supplies no child host and therefore uses NoRlmChildren: no delegated agent is launched. No daemon mode is started. Custom model pricing is unspecified; zero defaults are not a free-service claim.

## Resources

Linuxx64, declared2vCPU/2048MB, port9000,8GiB enforced rootfs budget within Express storage. No nested Docker/KVM/GPU needed. Model tool calling, explicit API access and egress are required for coding. Runtime peak-memory/workload capacity has not been measured.

## Verified

See [test results and scope](../docs/using-templates.md#evidence-and-providers). The dated records below identify the tested input and entry point.

## Secondary development

```bash
python -m pytest -q prime-agent/test_commands.py prime-agent/test_terminal.py
python scripts/check_template.py prime-agent --strict
python scripts/check_docs.py
python scripts/run_steps_e2e.py prime-agent
```

Real-model controller opts in only on an explicitly owned remote target. It repairs seeded existing source, preserves original test bytes, downloads a new report/exact fresh nonce, independently runs original3 plus4held-out cases and issues a fresh post-return ACK. Fixed synthetic protocol fixtures and source-only native skips do not establish a model/cloud pass.

## Contributing

Follow [CONTRIBUTING](../CONTRIBUTING.md), project/documentation standards and immutable evidence rules. Preserve original licenses and full release sidecars; update both README languages, design, manifest, catalog and engineering record together.

## Issues

Track [Issue69](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/69). Report sanitized reproducible wrapper/native/provider failures with source/version and explicit test tier. Never attach private keys/endpoints or raw prompts/model output.

SDK/server: [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues). CLI: [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).

## License

Authored wrapper Apache-2.0. Original Prime Agent MIT; original PHOTON third-party notice Apache-2.0. [Distribution and attribution](UPSTREAM-NOTICE.md); full upstream notices remain installed without relicensing.
