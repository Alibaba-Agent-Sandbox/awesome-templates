#!/usr/bin/env python3
"""Verify provider-managed builtins without replacing or deleting their definitions.

Current public CLI catalog launch and Python SDK. Credentials come from the environment. Each run
owns only its sandbox, records creation intent privately, and confirms absence.
"""
from __future__ import annotations
import argparse
import asyncio
from datetime import datetime, timezone
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
NAMES = ("base", "code-interpreter-v1")
INVENTORY = """import importlib.metadata,importlib.util,json,os,platform,shutil,subprocess
result={"os":platform.system(),"python":platform.python_version(),"non_root":os.geteuid()!=0,"kvm":os.path.exists('/dev/kvm'),"docker_socket":os.path.exists('/var/run/docker.sock')}
for name,args in {'node':['node','--version'],'git':['git','--version'],'bash':['bash','--version'],'curl':['curl','--version']}.items():
 result[name]=subprocess.run(args,capture_output=True,text=True,timeout=10).stdout.splitlines()[0] if shutil.which(args[0]) else None
result['python_packages']={}
for n in ['pip','numpy','pandas','matplotlib','jupyter','ipykernel']:
 try: result['python_packages'][n]=importlib.metadata.version(n)
 except importlib.metadata.PackageNotFoundError: result['python_packages'][n]=None
print(json.dumps(result))"""

async def verify(name: str, output: Path, cli: str | None) -> bool:
    from agent_sandbox import ProviderSandbox as Sandbox
    from agent_sandbox.models.errors import SandboxNotFoundError
    from public_launch_e2e import CLI, delete_sandbox
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    tag = "managed-proof-" + uuid.uuid4().hex
    private = Path(tempfile.mkdtemp(prefix="abx-managed-owned-"))
    private.chmod(0o700)
    journal = private / "intent.json"
    intent = {"metadata_tag": tag, "template": name, "create_attempted": True}
    def save():
        journal.write_text(json.dumps(intent) + "\n")
        journal.chmod(0o600)
    save()
    result = {"template": name, "provider": "alicloud-express", "verification_type": "provider-managed-runtime", "date": stamp, "passed": False, "cleanup_verified": False, "native_interpreter_verified": False, "checks": [], "client_version": importlib.metadata.version("agent-sandbox-client")}
    sb = None
    sandbox_id = None
    caller = CLI(cli, "alicloud-express", os.environ.copy()) if cli else None
    try:
        if caller:
            result["cli_version"] = caller.run(["--version"], json_output=False)
            launched = await asyncio.to_thread(caller.run, ["template", "launch", name,
                "--alias", tag[:42], "--sandbox-timeout", "240", "--yes"])
            sandbox_id = launched["sandbox_id"]
            intent["sandbox_id"] = sandbox_id
            save()
            sb = await Sandbox.connect(sandbox_id, provider="alicloud-express")
            result["checks"].append("public catalog bare-name CLI launch")
        else:
            sb = await Sandbox.create(template=name, provider="alicloud-express", timeout=240, metadata={"verification": tag})
            sandbox_id = sb.id
            intent["sandbox_id"] = sandbox_id
            save()
        import shlex
        command = "python3 -c " + shlex.quote(INVENTORY)
        observed = await sb.commands.run(command, timeout=60)
        assert observed.exit_code == 0
        result["inventory"] = json.loads(observed.stdout)
        assert result["inventory"]["non_root"] is True
        result["checks"].append("SDK shell and actual runtime inventory")
        path = "/tmp/managed-proof-" + uuid.uuid4().hex + ".txt"
        await sb.files.write(path, "owned-proof\n")
        assert await sb.files.read(path) == "owned-proof\n"
        await sb.files.remove(path)
        assert not await sb.files.exists(path)
        result["checks"].append("SDK file write/read/remove and absence")
        # Process/file acceptance makes no persistent interpreter-session claim.
        result["consumer"] = "public-cli-and-python" if caller else "python-provider"
        if caller:
            stdout = await asyncio.to_thread(caller.run, ["exec", sb.id, "--", "python3", "-c", "print(6*7)"], json_output=False)
            assert stdout.strip() == "42"
            result["checks"].append("real installed CLI exec result 42")
        if name == "code-interpreter-v1":
            code = 'import numpy,matplotlib,pandas as pd; print(pd.DataFrame({"x":[20,22]}).x.sum())'
            numeric = await sb.commands.run("python3 -c " + shlex.quote(code), timeout=60)
            assert numeric.exit_code == 0 and numeric.stdout.strip() == "42"
            result["checks"].append("actual numpy/pandas/matplotlib data processing")
        result["passed"] = True
    except Exception as exc:
        result["failure_type"] = type(exc).__name__
    finally:
        try:
            if sandbox_id:
                if caller:
                    try:
                        await asyncio.to_thread(caller.run, ["kill", sandbox_id], json_output=False)
                    except Exception as exc:
                        result["passed"] = False
                        result["cli_cleanup_failure_type"] = type(exc).__name__
                await delete_sandbox(Sandbox, sandbox_id, "alicloud-express", SandboxNotFoundError)
                result["cleanup_verified"] = True
                result["checks"].append("independent get-info confirms owned sandbox absent")
        except Exception as exc:
            result["cleanup_failure_type"] = type(exc).__name__
        if sb:
            try:
                await sb.close()
            except Exception as exc:
                result["passed"] = False
                result["client_close_failure_type"] = type(exc).__name__
        result["passed"] = result["passed"] and result["cleanup_verified"]
        intent["cleanup_verified"] = result["cleanup_verified"]
        save()
        output.mkdir(parents=True, exist_ok=True)
        with (output / (name + "-" + stamp + ".json")).open("x") as stream:
            json.dump(result, stream, indent=2)
            stream.write("\n")
        if result["cleanup_verified"]:
            journal.unlink()
            private.rmdir()
    print(name + ": " + ("PASS" if result["passed"] else "FAIL"), flush=True)
    return result["passed"]

async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("templates", nargs="+", choices=NAMES)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cli", help="Installed CLI executable (or quoted command), using public catalog launch and standard exec syntax")
    args = parser.parse_args()
    if len(set(args.templates)) != len(args.templates):
        parser.error("select unique template names")
    results = [await verify(n, args.output, args.cli) for n in args.templates]
    return int(not all(results))

if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
