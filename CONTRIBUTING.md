# Contributing to Awesome Templates for Agent Sandbox

[中文](CONTRIBUTING.zh-CN.md). Before implementation, read the
[project standards and definition of done](docs/project-standards.md),
[documentation standard](docs/documentation-standards.md), and
[engineering-record rules](.agents/README.md). These cover ownership, compatibility,
licenses, security, reproducibility, review, resource cleanup and Issue completion.

The rules for a template are [docs/template-spec.md](./docs/template-spec.md)
([中文](./docs/template-spec.zh-CN.md)). `_skeleton/` is a directory that
already passes `scripts/check_template.py`. It is not a catalog entry.

## Checklist

1. Copy `_skeleton/` to a kebab-case directory. The directory name,
   `template.yaml` `name`, and the index `path` are the same string.
2. Keep the default Express recipe's Alibaba base image, `generation: 2`,
   `start_cmd`, `ready_cmd`, pinned installs, and `USER user`. Do not add `CMD` or
   `ENTRYPOINT` to that recipe. A separately declared explicit build profile may
   use another pinned base; it must preserve the original recipe and non-root
   runtime, and is selected by name rather than applied as a provider rewrite.
3. Register named commands in `commands.py` with `@command`. Call `start()`
   only under `if __name__ == "__main__"`.
4. Fill `docs/design/<name>.md` from
   [docs/design/_TEMPLATE.md](./docs/design/_TEMPLATE.md).
5. Write `README.md` and `README.zh-CN.md` with the headings in the spec.
   The Verified section states the exact execution evidence scope; historical records do not certify the current manifest.
6. Add one `awesome-templates.yaml` entry. `official` means maintained by this
   project, `community` means externally maintained, and `experimental` marks
   development in progress. These labels do not certify runtime capabilities.
   Required component tests and exact provider/entry evidence remain mandatory;
   real-model claims require actual model tests.
7. From this repository, with `agent-sandbox-server`, `httpx`, and the pinned checker dependencies
   installed (`python3 -m pip install -r scripts/requirements-spec.txt`):

   ```bash
   python3 scripts/check_template.py <name>
   python3 scripts/run_local_e2e.py
   ```

   For actual source-launch acceptance, configure the selected provider and run:

   ```bash
   python scripts/public_launch_e2e.py <name> --provider alicloud-express --source ./<name> --output attempt.json
   ```

   Use `--provider opensandbox` for that backend. Follow the
   [public launch testing guide](docs/public-launch-testing.md) for installation,
   the two-platform matrix, assertions and independent owned-resource cleanup.
   Preserve failed attempts and unresolved cleanup; neither is a pass. The older
   `express_e2e.py` deployment harness belongs to the
   [pinned maintenance workflow](docs/canonical-express-review.md), not the current
   default user path. Do not copy its historical native flags into public CLI examples.

Do not commit `__pycache__/`, `.env`, or secret values. Declare secret
*names* with empty values in `template.yaml` `env`.

## Review and completion

The source directory remains authoritative across providers. Follow
[provider-owned preparation](docs/provider-preparation.md): each provider owns
base/image/registration adaptation; cross-cloud IDs are never converted.
Only the operations needed to launch the template are required; template-provided Python does not imply a unified interpreter dependency.
Catalog prerequisites and launch hints do not establish native backend acceptance.

Run `python scripts/check_docs.py` for local document links. Add a regression for
behavior-changing fixes; run affected tests and applicable CI gates. Keep both
README languages, command schemas and design current. Every contribution includes
an indexed `.agents/` decision and dated verification, with failures and skipped
or blocked checks distinguished from passes.

Reuse the matching Issue and verify every acceptance criterion before closing it.
In particular, merging an experimental implementation does not fulfill an Issue's
required Express deployment or real-model run. Work on a scoped branch, use
Conventional Commits and the PR template, and merge only after latest-head checks
and required review pass. Confirm actual remote merge and cleanup. Preserve
historical evidence and unrelated work. See the complete
[definition of done](docs/project-standards.md#definition-of-done).

## Named commands

```python
from agent_sandbox.server import command, start


@command("hello", description="Say hello.")
def hello(name: str = "World") -> str:
    return f"Hello, {name}!"


if __name__ == "__main__":
    import os

    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
```

Callers use `abx run <sandbox-id> hello --arg name=Ada` or
`await client.commands.run("hello", name="Ada")` after `ProviderSandbox.connect(...)`
and `await sb.application_client(9000, token=...)`. The CLI launch starts the
application; creating another sandbox alone does not start that service. See
[the complete example](docs/using-templates.md#cli-sdk-and-http).
A shell string is `sb.commands.run("echo hi")` or `abx exec`.

## Where to file issues

| Topic | Repository |
|---|---|
| Templates, this catalog, the spec | [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues) |
| Python SDK or the in-sandbox server | [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), title prefix `[templates]` |
| `abx` CLI | [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues), title prefix `[templates]` |

## Naming

**Agent Sandbox.** CLI `abx`. Client package `agent-sandbox-client`
(`agent_sandbox`). `pip install agent-sandbox` is an unrelated project.
In-image package `agent-sandbox-server`
(`agent_sandbox.server`). GitHub `alibaba-agent-sandbox/awesome-templates`,
`alibaba-agent-sandbox/python-sdk`, and `alibaba-agent-sandbox/agent-sandbox`.
npm `@agent-sandbox/cli`.
