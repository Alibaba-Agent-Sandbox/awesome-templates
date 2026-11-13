#!/usr/bin/env python3
"""Create a dynamic sandbox and start this application's process with private runtime values."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import secrets
from pathlib import Path
from typing import Any

# Generated from scripts/runtime_runner.py; regenerate with scripts/sync_runtime_runners.py.
START_COMMAND = 'agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py'
RUNTIME_ENV_NAMES: tuple[str, ...] = ('ABX_LLM_API_KEY', 'ABX_LLM_BASE_URL', 'OPENCODE_API_KEY', 'OPENCODE_MODEL', 'OPENCODE_SERVER_PASSWORD', 'ABX_SERVER_TOKEN')


async def launch(args: argparse.Namespace, sandbox_type: Any = None, *, environ: dict[str, str] | None = None) -> dict[str, Any]:
    """Start one owned instance; preserve its identity until cleanup succeeds."""
    if sandbox_type is None:
        from agent_sandbox import ProviderSandbox
        sandbox_type = ProviderSandbox
    environment = os.environ if environ is None else environ
    env = {key: environment[key] for key in RUNTIME_ENV_NAMES if environment.get(key)}
    token = environment.get("ABX_SERVER_TOKEN") or secrets.token_urlsafe(32)
    env["ABX_SERVER_TOKEN"] = token
    session = Path(args.session)
    # Refuse replacing an existing session, including symlinks. No token is printed.
    descriptor = os.open(session, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    state: dict[str, Any] = {"provider": args.provider, "template_id": args.template, "application_token": token, "status": "creating"}
    sandbox = client = None
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        def save() -> None:
            stream.seek(0)
            json.dump(state, stream)
            stream.truncate()
            stream.flush()
            os.fsync(stream.fileno())
        def created(sandbox_id: str) -> None:
            state["sandbox_id"] = sandbox_id
            save()
        save()
        try:
            sandbox = await sandbox_type.create(template=args.template, provider=args.provider, timeout=args.timeout, envs=env, on_created=created)
            created(sandbox.id)
            client = await sandbox.start_server(command=START_COMMAND, token=token, env=env, wait=True, timeout=args.ready_timeout)
            # Health is unauthenticated; discovery also verifies the actual app token.
            await client.discover()
            state["status"] = "ready"
            save()
            return {"sandbox_id": sandbox.id, "provider": args.provider, "session_file": str(session), "status": "ready"}
        except BaseException:
            state["status"] = "failed"
            save()
            try:
                if sandbox is not None:
                    await sandbox.kill()
                    state["status"] = "deleted-after-failure"
                elif state.get("sandbox_id"):
                    await sandbox_type.kill_by_id(state["sandbox_id"], provider=args.provider)
                    state["status"] = "deleted-after-failure"
                save()
            except BaseException:
                state["status"] = "cleanup-required"
                save()
                raise RuntimeError("Application startup failed and cleanup is incomplete; use the private session file to recover the owned instance") from None
            raise RuntimeError("Application startup failed; see the private session file for the cleanup result") from None
        finally:
            for resource, method in ((client, "aclose"), (sandbox, "close")):
                if resource is not None:
                    try:
                        await getattr(resource, method)()
                    except Exception as error:
                        # A local transport close failure must not hide cloud cleanup status.
                        state.setdefault("local_close_errors", []).append(type(error).__name__)
                        save()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", required=True, help="Prepared template ID returned by abx deploy")
    parser.add_argument("--provider", default="alicloud-express")
    parser.add_argument("--timeout", type=int, default=1800, help="Instance lifetime in seconds")
    parser.add_argument("--ready-timeout", type=float, default=60, help="Application readiness deadline in seconds")
    parser.add_argument("--session", default=".sandbox-session.json", help="New private session file; existing files are never overwritten")
    args = parser.parse_args()
    if args.timeout < 1 or args.ready_timeout <= 0:
        parser.error("timeouts must be positive")
    try:
        result = asyncio.run(launch(args))
    except Exception as error:
        if isinstance(error, FileExistsError):
            parser.exit(1, "Session file exists; choose another --session path or clean up its owned instance first.\n")
        parser.exit(1, "Application startup failed. Inspect the private session file for resource and cleanup status.\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
