# Contributing to Awesome Templates for Agent Sandbox

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
7. From this repository, with `agent-sandbox-server`, `httpx`, and `pyyaml`
   installed:

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
   `abx --json template list --official-api` for ownership checks. Exit 0 and
   provider-pass evidence require successful owned sandbox/template cleanup.
   A failed or ambiguous deploy/create keeps a private `intent.json` outside the
   checkout containing only owned identifiers, never credentials. Reconcile with
   `python3 scripts/express_e2e.py --recover-intent PRIVATE_PATH` using the same
   account/provider configuration. Recovery matches exact aliases/template IDs;
   an empty inventory after an unknown response does not prove cancellation.
   Successful recovery does not turn the failed attempt into L2 acceptance.

Do not commit `__pycache__/`, `.env`, or secret values. Declare secret
*names* with empty values in `template.yaml` `env`.

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
`await sb.run("hello", name="Ada")` after `from agent_sandbox import Sandbox`
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
