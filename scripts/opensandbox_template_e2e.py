"""Qualify one actual source image on the original OpenSandbox Docker backend.

The keyless image workflow builds the exact Dockerfile and SDK wheel first.
Each job owns its original server, provider engine and containers. No cloud or
model credentials are used. Generic code.interpret remains unsupported; this
tests the source template's named API, not a fabricated provider capability.
"""
from __future__ import annotations

import argparse
import asyncio
import contextlib
import hashlib
import importlib.metadata
import json
import logging
import os
from pathlib import Path
import re
import shlex
import signal
import subprocess
import sys
import threading
import time
import urllib.request
import uuid

import yaml

from ci_image import context_sha256
from server_sdk_pin import server_commit
from template_http_acceptance import fixture_environment, run_controller

PINS = {"upstream": "30348cbdfe4b9cfd49e0963617aed357a8f1ac4c",
        "provider": "9d2cf07467ff0e36303e4c80cbfe9fbf0fd70c6d",
        "cli": "c8e8ad784323b8903505442cbc77d433a0d0367a",
        "sdk": "33f857f5a79fd10326652e9d03f15f3621d6b848"}


def docker_ids():
    return set(subprocess.check_output(["docker", "ps", "-aq", "--no-trunc"], text=True).split())


def inspect_image(reference):
    return json.loads(subprocess.check_output(["docker", "image", "inspect", reference], text=True))[0]


def require(report, value, label):
    if not value:
        report["failed_check"] = label
        raise AssertionError(label)
    report["checks"].append(label)


def safe_label(value, secrets=()):
    for secret in secrets:
        if secret:
            value = value.replace(secret, "[FIXTURE]")
    value = re.sub(r"https?://\S+|/[A-Za-z0-9_.@%/+-]+", "[LOCATION]", value)
    value = re.sub(r"\b[0-9a-fA-F-]{16,}\b", "[ID]", value)
    return value[:300]


async def exercise(source, work, image_ref, image_id, report):
    from agent_sandbox.api.sandbox import Sandbox
    from agent_sandbox.api.server_client import ServerClient
    from agent_sandbox.models.errors import SandboxNotFoundError, ProviderFeatureNotSupportedError

    manifest = yaml.safe_load((source / "template.yaml").read_text())
    server_env, controller_env, fixture_proof = fixture_environment(source.name)
    report["test_configuration"] = fixture_proof
    baseline = docker_ids()
    nonce = "source-owned-" + uuid.uuid4().hex
    sandbox = None
    sid = None
    owned = set()
    cleanup_errors = []
    try:
        resources = manifest.get("resources", {})
        sandbox = await Sandbox.create(provider="opensandbox", template=image_ref, timeout=1200,
            cpu=resources.get("cpu", 2), memory=resources.get("memory", 2048),
            envs={**{key: str(value) for key, value in manifest.get("env", {}).items()}, **server_env},
            metadata={"verification": nonce})
        sid = sandbox.id
        owned = docker_ids() - baseline
        (work / "owned-intent.json").write_text(json.dumps({"id": sid, "metadata": nonce,
                                                          "containers": sorted(owned)}))
        require(report, bool(sid) and sandbox.provider == "opensandbox", "actual SDK create")
        containers = json.loads(subprocess.check_output(["docker", "inspect", *sorted(owned)], text=True))
        main = [item for item in containers if sid in item["Name"] and item["Image"] == image_id]
        require(report, len(main) == 1, "independent Docker identity matches exact built image")
        # Use the real guest's bridge address, not a localhost service or a mock.
        addresses = [network.get("IPAddress") for network in main[0]["NetworkSettings"]["Networks"].values()
                     if network.get("IPAddress")]
        require(report, len(addresses) == 1, "actual guest bridge endpoint")
        host = addresses[0]
        info = await sandbox.refresh_info()
        require(report, info.metadata.get("verification") == nonce, "owned metadata readback")
        observed = await sandbox.files.read("/home/user/app/commands.py")
        require(report, observed.encode() == (source / "commands.py").read_bytes(), "actual runtime command bytes match source")
        # Preserve the actual image USER. Legacy execd cannot always repeat a
        # same-identity uid/gid switch without CAP_SETGID; that option is not
        # needed to run the already non-root profile and is not qualified here.
        result = await sandbox.commands.run("id -u", timeout=30)
        report["execution_identity"] = {"selection": "image default; explicit user switching not qualified",
            "probe_exit_code": result.exit_code,
            "uid": int(result.stdout.strip()) if result.stdout.strip().isdigit() else None}
        require(report, result.exit_code == 0 and result.stdout.strip().isdigit()
                and int(result.stdout.strip()) > 0, "SDK observes actual non-root image user")
        result = await sandbox.commands.run("python3 -c 'print(6*7)'", timeout=30)
        require(report, result.exit_code == 0 and result.stdout.strip() == "42", "SDK real shell Python program")
        path = "/tmp/" + nonce + ".txt"
        await sandbox.files.write(path, "owned-file\n")
        require(report, await sandbox.files.read(path) == "owned-file\n", "SDK file write/read")
        await sandbox.files.remove(path)
        require(report, not await sandbox.files.exists(path), "SDK file removal readback")
        # Explicitly preserve the provider capability boundary.
        try:
            await sandbox.run_code("print(42)")
        except ProviderFeatureNotSupportedError as exc:
            require(report, exc.code == "E8004", "generic native interpreter explicitly unsupported")
        else:
            raise AssertionError("unexpected unqualified code.interpret")
        startup = manifest["start_cmd"]
        command = "nohup /bin/sh -c " + shlex.quote(startup) + " >/tmp/abx-source-service.log 2>&1 </dev/null &"
        result = await sandbox.commands.run(command, cwd="/home/user/app", timeout=30)
        require(report, result.exit_code == 0, "SDK starts original template service as user")
        for _ in range(120):
            result = await sandbox.commands.run(manifest["ready_cmd"], timeout=5)
            if result.exit_code == 0:
                break
            await asyncio.sleep(.5)
        else:
            raise RuntimeError("template readiness timeout")
        require(report, True, "original template readiness command")
        base = f"http://{host}:9000"
        client = ServerClient(base, token=None, timeout=180)
        try:
            for smoke in manifest["smoke"]:
                value = await client.commands.run(smoke["command"], timeout=180, **smoke.get("args", {}))
                expected = smoke.get("expect")
                if expected is not None:
                    equal = value.strip() == expected.strip() if isinstance(value, str) and isinstance(expected, str) else value == expected
                    require(report, equal, "SDK named smoke " + smoke["command"])
                else:
                    require(report, value is not None, "SDK named smoke " + smoke["command"])
        finally:
            await client.aclose()
        urls = {port: f"http://{host}:{port}" for port in manifest.get("ports", [9000])}
        # The controller is synchronous and may call the same running server.
        report["http_acceptance"] = await asyncio.to_thread(run_controller, source, urls, work, controller_env)
        if not report["http_acceptance"]["passed"]:
            labels = [line for line in (work / "http.log").read_text().splitlines() if line.startswith(("[FAIL]", "[SKIP]"))]
            report["http_diagnostics"] = [safe_label(label, server_env.values()) for label in labels[:12]]
        require(report, report["http_acceptance"]["passed"], "complete current external HTTP controller")
    finally:
        # Reconcile uncertain create using only this authored metadata.
        if sandbox is None:
            try:
                matches = [item for item in await Sandbox.list(provider="opensandbox")
                           if item.metadata.get("verification") == nonce]
                for item in matches:
                    await Sandbox.kill_by_id(item.sandbox_id, provider="opensandbox")
                    sid = item.sandbox_id
                owned = docker_ids() - baseline
            except Exception as exc:
                cleanup_errors.append(type(exc).__name__)
        else:
            try:
                await sandbox.kill()
            except Exception as exc:
                cleanup_errors.append(type(exc).__name__)
            finally:
                await sandbox.close()
        sdk_absent = sid is None
        docker_absent = False
        for _ in range(120):
            if sid:
                try:
                    await Sandbox.get_info_by_id(sid, provider="opensandbox")
                except SandboxNotFoundError:
                    sdk_absent = True
                except Exception:
                    pass
            docker_absent = not (owned & docker_ids()) and docker_ids() == baseline
            if sdk_absent and docker_absent:
                break
            await asyncio.sleep(.5)
        report["cleanup_observations"] = {"sdk_not_found": sdk_absent,
            "owned_docker_containers_absent": docker_absent, "errors": cleanup_errors}
        report["cleanup_verified"] = sdk_absent and docker_absent and not cleanup_errors
        require(report, report["cleanup_verified"], "independent SDK and Docker absence")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("template", type=Path)
    parser.add_argument("--image", required=True)
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source, fixtures, work = args.template.resolve(), args.fixtures.resolve(), args.work.resolve()
    work.mkdir(parents=True, exist_ok=False)
    work.chmod(0o700)
    home = work / "home"
    home.mkdir()
    manifest = yaml.safe_load((source / "template.yaml").read_text())
    report = {"provider": "opensandbox", "template": source.name, "template_version": str(manifest["version"]),
              "verification_type": "source-image-native-opensandbox-docker-http", "build_mode": "image",
              "passed": False, "cleanup_verified": False, "model_acceptance": "NOT_RUN", "checks": [], "pins": PINS,
              "source_commit": subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip(),
              "context_sha256": context_sha256(source), "server_sdk_commit": server_commit(source),
              "workflow_run_id": os.environ.get("GITHUB_RUN_ID"),
              "generic_code_interpretation": "UNSUPPORTED; template named APIs tested separately"}
    os.environ["HOME"] = str(home)
    os.environ["ABX_BIN"] = shlex.join(["node", str(fixtures / "cli/dist/bin/abx.js")])
    os.environ.update(ABX_OPENSANDBOX_BASE_URL="http://127.0.0.1:8080",
        ABX_OPENSANDBOX_API_KEY="fixed-synthetic-opensandbox-key", OPEN_SANDBOX_USE_SERVER_PROXY="true")
    logging.disable(logging.CRITICAL)
    server = None
    failed = False
    started = time.monotonic()
    with (work / "private-controller.log").open("w") as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        try:
            for name, expected in PINS.items():
                actual = subprocess.check_output(["git", "-C", str(fixtures / ("providers" if name == "provider" else name)), "rev-parse", "HEAD"], text=True).strip()
                require(report, actual == expected, "fixed source " + name)
            image = inspect_image(args.image)
            require(report, image["Architecture"] == "amd64" and image["Os"] == "linux"
                    and image["Config"]["User"] == "user" and image["Config"]["WorkingDir"] == "/home/user/app",
                    "actual image architecture and non-root workspace configuration")
            execd = inspect_image("opensandbox/execd:v1.1.0")
            digest = next(value for value in execd["RepoDigests"] if value.startswith("opensandbox/execd@sha256:"))
            report["images"] = {"template_image_id": image["Id"], "execd_digest": digest, "execd_image_id": execd["Id"]}
            config = work / "server.toml"
            config.write_text('[server]\nhost="127.0.0.1"\nport=8080\napi_key="fixed-synthetic-opensandbox-key"\n[runtime]\ntype="docker"\nexecd_image=' + json.dumps(digest) + '\n[store]\ntype="sqlite"\npath=' + json.dumps(str(work / "server.db")) + '\n[docker]\nnetwork_mode="bridge"\npublish_host="127.0.0.1"\n[ingress]\nmode="direct"\n')
            config.chmod(0o600)
            server = subprocess.Popen([str(fixtures / "upstream/server/.venv/bin/opensandbox-server"), "--config", str(config)],
                stdout=log, stderr=log, start_new_session=True,
                env={"PATH": os.environ["PATH"], "HOME": str(home), "LANG": "C.UTF-8"})
            for _ in range(120):
                if server.poll() is not None:
                    raise RuntimeError("original server exited before health")
                try:
                    with urllib.request.urlopen("http://127.0.0.1:8080/health", timeout=2) as response:
                        if response.status == 200:
                            break
                except OSError:
                    pass
                time.sleep(.5)
            else:
                raise RuntimeError("original server health timeout")
            require(report, True, "original OpenSandbox server health")
            subprocess.run([sys.executable, "-m", "agent_sandbox.providers", "install", str(fixtures / "providers/opensandbox"), "--yes"], stdout=log, stderr=log, check=True)
            asyncio.run(exercise(source, work, args.image, image["Id"], report))
            report["versions"] = {name: importlib.metadata.version(name) for name in ["agent-sandbox-client", "agent-sandbox-server", "opensandbox-server"]}
        except Exception as exc:
            failed = True
            report["error_type"] = type(exc).__name__
            report["error_message"] = safe_label(str(exc))
        finally:
            try:
                record = home / ".abx/engine.json"
                waiter = None
                if record.exists():
                    pid = int(json.loads(record.read_text())["pid"])
                    def reap():
                        try:
                            os.waitpid(pid, 0)
                        except ChildProcessError:
                            pass
                    waiter = threading.Thread(target=reap, daemon=True)
                    waiter.start()
                stopped = subprocess.run(shlex.split(os.environ["ABX_BIN"]) + ["provider", "engine", "stop"], stdout=log, stderr=log, timeout=15)
                if waiter:
                    waiter.join(timeout=5)
                require(report, stopped.returncode == 0 and (not waiter or not waiter.is_alive()), "owned provider engine stopped and reaped")
            except Exception as exc:
                failed = True
                report["engine_cleanup_error"] = type(exc).__name__
            if server:
                try:
                    os.killpg(server.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    server.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(server.pid, signal.SIGKILL)
                    server.wait(timeout=5)
                require(report, server.poll() is not None, "owned original server process stopped")
    report["passed"] = not failed and report["cleanup_verified"] and report.get("http_acceptance", {}).get("passed") is True
    report["duration_s"] = round(time.monotonic() - started, 3)
    report["controller_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    if os.environ.get("GITHUB_ACTIONS") == "true":
        notice = json.dumps(report, separators=(",", ":")).replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        print("::notice title=Sanitized native source OpenSandbox receipt::" + notice)
    print(json.dumps({key: report.get(key) for key in ["template", "passed", "cleanup_verified", "error_type", "failed_check"]}), flush=True)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
