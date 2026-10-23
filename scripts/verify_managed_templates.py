#!/usr/bin/env python3
"""Verify provider-managed builtins without replacing or deleting their definitions.

Native SDK and CLI 0.3 syntax. Credentials come from the environment. Each run
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
    from agent_sandbox.api.sandbox import Sandbox
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
    try:
        sb = await Sandbox.create(template=name, timeout=240, metadata={"verification": tag})
        intent["sandbox_id"] = sb.id
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
        # This managed workflow selects exec. It makes no unified interpreter claim.
        result["classification"] = "local-report"
        result["workflow_id"] = "exec"
        result["consumer"] = "python-provider"
        if cli:
            proc = await asyncio.create_subprocess_exec(cli, "--json", "exec", sb.id, "--", "python3", "-c", "print(6*7)", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            try:
                stdout, _ = await asyncio.wait_for(proc.communicate(), 90)
            except BaseException:
                if proc.returncode is None:
                    proc.kill()
                await proc.communicate()
                raise
            assert proc.returncode == 0 and "42" in stdout.decode()
            result["checks"].append("real native CLI exec result 42")
        result["passed"] = True
    except Exception as exc:
        result["failure_type"] = type(exc).__name__
    finally:
        try:
            if sb:
                await sb.kill()
                await sb.close()
            offset = 0
            matches = []
            while True:
                rows = await Sandbox.list(limit=100, offset=offset)
                matches.extend(x for x in rows if (x.metadata or {}).get("verification") == tag)
                if len(rows) < 100:
                    break
                offset += len(rows)
            # A lost create response cannot prove cancellation from empty inventory.
            result["cleanup_verified"] = sb is not None and not matches
        except Exception as exc:
            result["cleanup_failure_type"] = type(exc).__name__
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
    parser.add_argument("--cli", help="Native CLI executable with --json exec syntax")
    args = parser.parse_args()
    if len(set(args.templates)) != len(args.templates):
        parser.error("select unique template names")
    results = [await verify(n, args.output, args.cli) for n in args.templates]
    return int(not all(results))

if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
