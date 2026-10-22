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
2. Keep the Alibaba base image, `generation: 2`, `start_cmd`, `ready_cmd`,
   pinned installs, and `USER user`. Do not add `CMD` or `ENTRYPOINT`.
3. Register named commands in `commands.py` with `@command`. Call `start()`
   only under `if __name__ == "__main__"`.
4. Fill `docs/design/<name>.md` from
   [docs/design/_TEMPLATE.md](./docs/design/_TEMPLATE.md).
5. Write `README.md` and `README.zh-CN.md` with the headings in the spec.
   The Verified section lists only providers that have a passing evidence file.
6. Add one `awesome-templates.yaml` entry. Use `experimental` until L0, L1,
   and L2 have passed. `official` also needs L3 before the README says the
   upstream agent works.
7. From this repository, with `agent-sandbox-server`, `httpx`, and the pinned checker dependencies
   installed (`python3 -m pip install -r scripts/requirements-spec.txt`):

   ```bash
   python3 scripts/check_template.py <name>
   python3 scripts/run_local_e2e.py
   ```

   With Express credentials, `python3 scripts/express_e2e.py <name>` is L2.
   Concurrent runs share `/tmp/abx-acr-push.lock` so only one ACR push is
   active. A deploy dies when CLI output is idle for `--idle-timeout` seconds
   (default 180), then retries. Commit `evidence/express-<date>.json` only
   when that command exits 0. `python3 scripts/image_size_report.py IMAGE`
   prints per-layer sizes.

   The runner refuses an existing official template alias and requires
   `abx --json template list` for ownership checks. Exit 0 and
   provider-pass evidence require successful owned sandbox/template cleanup.
   The runner independently reads back known sandbox IDs/templates and the exact
   official alias before publishing; cleanup acknowledgements alone are insufficient.
   A failed or ambiguous deploy/create keeps a private `intent.json` outside the
   checkout containing only owned identifiers, never credentials. Reconcile with
   `python3 scripts/express_e2e.py --recover-intent PRIVATE_PATH` using the same
   account/provider configuration. Recovery matches exact aliases/template IDs;
   an empty inventory after an unknown response does not prove cancellation.
   Successful recovery does not turn the failed attempt into L2 acceptance.
   The deploy explicitly uses the owned alias as ACR repository and the fixed
   temporary tag `review`; plan/private intent records both. Registry image
   retention/deletion is separate from the runner's sandbox/template cleanup.

Do not commit `__pycache__/`, `.env`, or secret values. Declare secret
*names* with empty values in `template.yaml` `env`.

## Review and completion

The source directory remains authoritative across providers. Follow
[provider-owned preparation](docs/provider-preparation.md): each provider owns
base/image/registration adaptation; cross-cloud IDs are never converted.
Missing terminal/code or other required capabilities stay unsupported.
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
`await sb.run("hello", name="Ada")` after `from agent_sandbox.api.sandbox import Sandbox`
and `await Sandbox.create(...)`.
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
