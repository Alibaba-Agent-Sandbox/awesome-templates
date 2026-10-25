#!/usr/bin/env python3
"""Run real Express step acceptance serially, retaining sanitized per-attempt receipts.

Credentials come from the environment. ABX selects the verified CLI command.
Private harness journals/logs remain outside the checkout. This does not run L3.
"""
from __future__ import annotations

import argparse
import asyncio
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
import hashlib
import json
import os
import secrets
from pathlib import Path
import tempfile
import sys
import time
import uuid

import yaml

import express_e2e
from prepare_steps import ROOT, parallel_assets, prepare
from select_image_templates import catalog_names


def configure_http_fixture(source: Path, manifest: dict, proof: dict) -> dict[str, str]:
    """Configure an owned non-model gateway after installer RUNs, never in Git."""
    if source.name == 'devin':
        if manifest.get('env',{}).get('DEVIN_CREDENTIALS_FILE')not in ['',None]:raise ValueError('native no-account fixture cannot configure credentials')
        proof['test_configuration']={'native_authentication_error_path_required':True,'credential_absence_required':True,'model_credentials_injected':False}
        return {}
    if source.name == 'cursor-agent':
        steps=manifest['build']['steps']
        if steps[-1]!={'type':'USER','args':['user']}:raise ValueError('Cursor native fixture requires the reviewed non-root profile')
        steps.insert(len(steps)-1,{'type':'ENV','args':['CURSOR_API_KEY','key_'+'a'*64]})
        manifest.setdefault('env',{})['CURSOR_API_KEY']='key_'+'a'*64
        size=len(json.dumps(steps,ensure_ascii=False).encode())
        if size>15000:raise ValueError('Cursor native fixture exceeds unchanged wire budget')
        proof['steps_json_bytes']=size
        proof['generated_manifest_sha256']=hashlib.sha256(yaml.safe_dump(manifest,sort_keys=False,allow_unicode=True).encode()).hexdigest()
        proof['test_configuration']={'native_authentication_error_path_required':True,'synthetic_invalid_vendor_credential':True,'model_credentials_injected':False}
        return {}
    if source.name == "osworld":
        proof["test_configuration"] = {"desktop_lifecycle_required": True, "model_credentials_injected": False}
        return {}
    if source.name != "openclaw":
        return {}
    token = secrets.token_urlsafe(32)
    steps = manifest["build"]["steps"]
    if steps[-1] != {"type": "USER", "args": ["user"]}:
        raise ValueError("gateway fixture requires the reviewed non-root profile")
    steps.insert(len(steps) - 1, {"type": "ENV", "args": ["OPENCLAW_GATEWAY_TOKEN", token]})
    size = len(json.dumps(steps, ensure_ascii=False).encode())
    if size > 15000:
        raise ValueError("gateway fixture exceeds the unchanged step wire budget")
    proof["steps_json_bytes"] = size
    proof["generated_manifest_sha256"] = hashlib.sha256(yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True).encode()).hexdigest()
    proof["test_configuration"] = {"gateway_lifecycle_required": True, "generated_test_token": True,
                                   "model_credentials_injected": False}
    return {"OPENCLAW_GATEWAY_TOKEN": token}


def http_callback(source: Path, stage: Path, result: dict, fixture_env: dict[str, str] | None = None):
    """Run the unchanged external controller once, inside canonical ownership."""
    done = False
    if fixture_env and (source.name != "openclaw" or set(fixture_env) != {"OPENCLAW_GATEWAY_TOKEN"}):
        raise ValueError("only the generated owned gateway fixture may enter the controller")

    async def endpoints(sandbox_id):
        from agent_sandbox import ProviderSandbox
        sandbox = await ProviderSandbox.connect(sandbox_id)
        try:
            ports = yaml.safe_load((source / "template.yaml").read_text()).get("ports", [9000])
            return {port: sandbox.network.get_url(port) for port in ports}
        finally:
            await sandbox.close()

    def sdk(sandbox_id, command, arguments):
        nonlocal done
        value = express_e2e.default_sdk(sandbox_id, command, arguments)
        if done:
            return value
        done = True
        urls = asyncio.run(endpoints(sandbox_id))
        # The controller needs only forwarded sandbox URLs. Cloud credentials
        # and the operator's model credentials never enter this subprocess.
        env = {key: val for key, val in os.environ.items()
               if not any(part in key.upper() for part in
                          ("TOKEN", "API_KEY", "SECRET", "PASSWORD", "ACCESS_KEY"))}
        env.update(E2E_BASE_URL=urls[9000], E2E_BASE_DIR="/home/user/app",
                   E2E_WORKSPACE="/home/user/app", E2E_RUN_LLM="0", E2E_REQUIRE_CLI="1",
                   E2E_REQUIRE_LLM="0",
                   E2E_REQUIRE_OCR="1", E2E_REQUIRE_DATABASES="1", E2E_REQUIRE_TOOLCHAIN="1")
        if source.name == "osworld":
            env.update(E2E_RUN_DESKTOP="1", E2E_REQUIRE_DESKTOP="1")
        if source.name == 'devin':
            env.update(E2E_DEVIN_NO_ACCOUNT_FIXTURE='1',E2E_REMOTE_SANDBOX='1')
        if source.name == 'cursor-agent':
            env.update(E2E_CURSOR_INVALID_KEY_FIXTURE='1',E2E_REMOTE_SANDBOX='1')
        env.update(fixture_env or {})
        if source.name == "code-server":
            env["E2E_CODE_SERVER_URL"] = urls[8443]
        if source.name == "next-app":
            env.update(E2E_NEXT_URL=urls[3000], E2E_VITE_URL=urls[5173])
        if source.name == "chrome":
            env.update(E2E_CHROME_CDP_URL=urls[9222], E2E_CHROME_VNC_URL=urls[6080],
                       E2E_WORKSPACE="/home/user/workspace", E2E_REQUIRE_CHROME="1")
        script = source / "e2e_test.py"
        response = express_e2e.run_monitored([sys.executable, str(script)], env=env,
                                            idle_timeout=600, wall_timeout=600)
        (stage / "private-http.log").write_text(response.stdout + "\n" + response.stderr)
        lines = (response.stdout + "\n" + response.stderr).splitlines()
        checks = {"exit_code": response.returncode,
                  "pass_count": sum(line.startswith("[PASS]") for line in lines),
                  "fail_count": sum(line.startswith("[FAIL]") for line in lines),
                  "skip_count": sum(line.startswith("[SKIP]") for line in lines),
                  "controller_sha256": hashlib.sha256(script.read_bytes()).hexdigest()}
        result["http_acceptance"] = checks
        if source.name=='devin'and(checks['skip_count']or checks['pass_count']<16):
            raise RuntimeError('original Devin native HTTP/SDK no-account fixture was skipped or incomplete')
        if source.name=='cursor-agent'and(checks['skip_count']or checks['pass_count']<16):
            raise RuntimeError('original Cursor native HTTP/SDK auth-refusal fixture was skipped or incomplete')
        if source.name == "openclaw" and (not fixture_env or any(line.startswith("[SKIP] real gateway lifecycle") for line in lines)):
            raise RuntimeError("non-model gateway lifecycle was skipped; full acceptance refused")
        if source.name == "osworld" and (checks["skip_count"] or checks["pass_count"] < 18):
            raise RuntimeError("non-model desktop lifecycle was skipped or incomplete; full acceptance refused")
        if source.name == "chrome" and checks["skip_count"]:
            raise RuntimeError("native Chrome desktop was skipped; full acceptance refused")
        if response.returncode or checks["fail_count"] or not checks["pass_count"]:
            raise RuntimeError("external HTTP controller failed; private diagnostics retained")
        return value

    return sdk


def run_one(name: str, args: argparse.Namespace) -> dict:
    source = ROOT / name
    started = time.monotonic()
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    stage = Path(tempfile.mkdtemp(prefix="abx-step-stage-"))
    stage.chmod(0o700)
    result = {"template": name, "provider": "alicloud-express", "build_mode": "steps",
              "attempt": stamp, "result": "FAIL", "passed": False, "model_acceptance": "NOT_RUN"}
    cache = None
    try:
        if args.http:
            from run_ci_image_e2e import controller_missing_imports
            missing = controller_missing_imports(source)
            if missing:
                result["missing_controller_modules"] = missing
                raise RuntimeError("missing local HTTP controller prerequisites")
        cache_config = None
        if args.asset_transport == "oss" and parallel_assets(source):
            from step_asset_cache import AssetCache
            cache = AssetCache(args.region)
            cache_config = cache.prepare(parallel_assets(source))
        manifest, proof = prepare(source, region=args.region, tag=args.base_tag,
                                  base_path=args.base_path,
                                  asset_transport=args.asset_transport, asset_cache=cache_config)
        fixture_env = configure_http_fixture(source, manifest, proof) if args.http else {}
        (stage / "template.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True))
        (stage / "steps-provenance.json").write_text(json.dumps(proof, indent=2) + "\n")
        result["build_provenance"] = proof
        options = express_e2e.build_options([str(stage), "--build", "steps", "--alias",
            f"e2e-steps-{name}-{uuid.uuid4().hex[:8]}", "--timeout", str(args.timeout),
            "--idle-timeout", str(args.timeout), "--wall-timeout", str(args.timeout + 180),
            "--push-retries", "0", "--sandbox-create", args.sandbox_create,
            "--sandbox-timeout", "1200" if args.http else "300"])
        callback = http_callback(source, stage, result, fixture_env) if args.http else None
        def verify_owned(intent, runner):
            observed = express_e2e.owned_resources_absent(intent, runner)
            result["cleanup_verified"] = observed
            return observed
        with (stage / "private-harness.log").open("x") as output, redirect_stdout(output), redirect_stderr(output):
            status = express_e2e.execute(options, sdk=callback, verify=verify_owned)
        result["exit_code"] = status
        if status == 0:
            receipts = list((stage / "evidence").glob("express-*.json"))
            if len(receipts) != 1:
                raise RuntimeError("missing unique successful step receipt")
            receipt = json.loads(receipts[0].read_text())
            if any(value in json.dumps(receipt) for value in fixture_env.values()):
                raise RuntimeError("refusing public evidence containing a generated runtime credential")
            if receipt.get("cleanup_verified") is not True or receipt.get("build_mode") != "steps":
                raise RuntimeError("step receipt lacks required cleanup/build-mode evidence")
            if cache:
                if not cache.cleanup():
                    raise RuntimeError("private asset-cache cleanup was not independently verified")
                receipt["asset_cache"] = cache.public_proof()
            target = source / "evidence" / receipts[0].name
            target.parent.mkdir(exist_ok=True)
            if target.exists():
                target = target.with_name("express-" + stamp + ".json")
            # Exclusive creation preserves every historical receipt.
            with target.open("x") as stream:
                json.dump(receipt, stream, indent=2, ensure_ascii=False)
                stream.write("\n")
            result.update(result="PASS", passed=True, cleanup_verified=True,
                          receipt=str(target.relative_to(ROOT)), command_calls=len(receipt["commands"]))
        else:
            result["reason"] = "canonical step harness failed; private diagnostics/journal retained"
            result["result"] = "BLOCKED" if status == 2 else "FAIL"
    except Exception as exc:
        result["reason"] = type(exc).__name__ + "; private staging retained"
    finally:
        if cache:
            try:
                if not cache.cleanup():
                    result.update(passed=False, result="FAIL", reason="asset-cache cleanup is not independently verified")
            except Exception:
                result.update(passed=False, result="FAIL", reason="asset-cache cleanup requires private owned recovery")
            result["asset_cache"] = cache.public_proof()
    result["duration_s"] = round(time.monotonic() - started, 3)
    evidence = source / "evidence"
    evidence.mkdir(exist_ok=True)
    path = evidence / ("verification-steps-" + stamp + ".json")
    with path.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(f"{name}: {result['result']} ({result['duration_s']}s); {path.relative_to(ROOT)}", flush=True)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("templates", nargs="*")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--region", default="cn-hangzhou")
    parser.add_argument("--base-tag", default="v0.0.49")
    parser.add_argument("--base-path", help="Verified base PATH when selecting a different image tag")
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--sandbox-create", choices=("cli", "sdk"), default="cli")
    parser.add_argument("--http", action="store_true", help="Also run the unchanged full external HTTP controller; model cases remain explicitly skipped")
    parser.add_argument("--asset-transport", choices=("direct", "parallel", "oss"), default="direct",
                        help="OSS uses a temporary private same-account cache for verified official archives; requires optional local OSS SDK")
    args = parser.parse_args()
    names = catalog_names()
    selected = names if args.all else args.templates
    if not selected or len(set(selected)) != len(selected) or any(name not in names for name in selected):
        parser.error("select unique catalog names or --all")
    results = [run_one(name, args) for name in selected]
    return int(any(not row["passed"] for row in results))


if __name__ == "__main__":
    raise SystemExit(main())
