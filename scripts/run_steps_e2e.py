#!/usr/bin/env python3
"""Run real Express step acceptance serially, retaining sanitized per-attempt receipts.

Credentials come from the environment. ABX selects the verified CLI command.
Private harness journals/logs remain outside the checkout. This does not run L3.
"""
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
import shutil
import subprocess
import time
import uuid

import yaml

from prepare_steps import ROOT, parallel_assets, prepare
from select_image_templates import catalog_names


def run_one(name: str, args: argparse.Namespace) -> dict:
    source = ROOT / name
    verifier_commit = subprocess.check_output(['git', '-C', str(Path(__file__).resolve().parents[1]),
        'rev-parse', 'HEAD'], text=True).strip()
    started = time.monotonic()
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    stage = Path(tempfile.mkdtemp(prefix="abx-step-stage-"))
    stage.chmod(0o700)
    result = {"template": name, "provider": "alicloud-express", "build_mode": "steps",
              "attempt": stamp, "verifier_commit": verifier_commit, "result": "FAIL", "passed": False, "model_acceptance": "NOT_RUN",
              "preparation_attempted": False, "runtime_attempted": False, "cleanup_verified": False, "template_cleanup_verified": False}
    cache = None
    try:
        from run_ci_image_e2e import controller_missing_imports, exercise, exact_templates, wait_ready, delete_owned_templates
        from public_launch_e2e import CLI, require
        from ci_image_archive import save_private
        missing = controller_missing_imports(source)
        if missing:
            result['missing_controller_modules'] = missing
            raise RuntimeError('missing local HTTP controller prerequisites')
        cli = CLI(os.environ.get('ABX', 'abx'), 'alicloud-express', os.environ.copy())
        native_help = cli.run(['template', 'deploy', '--help'], native=True, json_output=False)
        require(all(flag in native_help for flag in ['--build', '--alias', '--generation', '--start-cmd', '--ready-cmd']),
                'current native step preparation contract')
        cache_config = None
        if args.asset_transport == "oss" and parallel_assets(source):
            from step_asset_cache import AssetCache
            cache = AssetCache(args.region)
            cache_config = cache.prepare(parallel_assets(source))
        manifest, proof = prepare(source, region=args.region, tag=args.base_tag,
                                  base_path=args.base_path,
                                  asset_transport=args.asset_transport, asset_cache=cache_config)
        # Native preparation builds an idle template. The current shared launch
        # consumer owns the original application's startup, env and readiness.
        manifest.pop('start_cmd', None)
        manifest.pop('ready_cmd', None)
        (stage / 'template.yaml').write_text(yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True))
        proof['generated_manifest_sha256'] = hashlib.sha256((stage / 'template.yaml').read_bytes()).hexdigest()
        (stage / 'steps-provenance.json').write_text(json.dumps(proof, indent=2) + '\n')
        result['build_provenance'] = proof
        result['template_version'] = str(yaml.safe_load((source / 'template.yaml').read_text())['version'])
        alias = 'e2e-steps-' + name[:24] + '-' + uuid.uuid4().hex[:8]
        require(not exact_templates(cli, alias), 'unique native step alias preflight')
        intent_path = stage / 'platform-intent.json'
        save_private(intent_path, {'alias': alias, 'preflight_absent': True,
                                  'registration_attempted': True, 'sandbox_ids': []})
        try:
            result["preparation_attempted"] = True
            deployed = cli.run(['template', 'deploy', str(stage), '--build', 'steps',
                '--generation', '2', '--start-cmd', '', '--ready-cmd', '',
                '--alias', alias, '--timeout', str(args.timeout), '--yes'], args.timeout + 180, native=True)
            template_id = deployed['TemplateID']
            require(isinstance(template_id, str) and bool(template_id.strip()), 'native step template identifier')
            intent = json.loads(intent_path.read_text());intent['template_id'] = template_id
            save_private(intent_path, intent)
            wait_ready(cli, template_id, args.timeout)
            result['runtime_attempted'] = True
            asyncio.run(exercise(source, template_id, stage, result, True, intent_path,
                                 runtime_env=manifest.get('env', {})))
        finally:
            clean = True
            try:
                known = json.loads(intent_path.read_text()).get('template_id')
                clean = delete_owned_templates(cli, alias, known)
            except Exception as failure:
                clean = False
                result['template_cleanup_failure_type'] = type(failure).__name__
            result['template_cleanup_verified'] = clean
            intent = json.loads(intent_path.read_text());intent['template_cleanup_verified'] = clean
            save_private(intent_path, intent)
        if (result.get('application_result') != 'PASS' or result.get('cleanup_verified') is not True
                or result.get('template_cleanup_verified') is not True or result.get('local_close_errors')):
            raise RuntimeError('current launch/controller or owned cleanup did not pass')
        result.update(result='PASS', passed=True, command_calls=len(result['commands']))
    except Exception as exc:
        result["reason"] = type(exc).__name__ + "; private staging retained"
        from public_launch_e2e import safe_failure_label, safe_diagnostics
        result['diagnostics'] = safe_diagnostics(exc)
        if safe_failure_label(exc):
            result['failed_check'] = safe_failure_label(exc)
    finally:
        if cache:
            try:
                if not cache.cleanup():
                    result.update(passed=False, result="FAIL", reason="asset-cache cleanup is not independently verified")
            except Exception:
                result.update(passed=False, result="FAIL", reason="asset-cache cleanup requires private owned recovery")
            result["asset_cache"] = cache.public_proof()
    result['unresolved_owned_cleanup'] = bool(
        result.get('preparation_attempted') and result.get('template_cleanup_verified') is not True
        or result.get('runtime_attempted') and result.get('cleanup_verified') is not True
        or result.get('asset_cache') and result['asset_cache'].get('cleanup_verified') is not True)
    result["duration_s"] = round(time.monotonic() - started, 3)
    evidence = source / "evidence"
    evidence.mkdir(exist_ok=True)
    path = evidence / ("verification-steps-" + stamp + ".json")
    with path.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    if result["passed"]:
        shutil.rmtree(stage)
    else:
        print("Private attempt retained at " + str(stage), flush=True)
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
    parser.add_argument("--asset-transport", choices=("direct", "parallel", "oss"), default="direct",
                        help="OSS uses a temporary private same-account cache for verified official archives; requires optional local OSS SDK")
    args = parser.parse_args()
    names = catalog_names()
    selected = names if args.all else args.templates
    if not selected or len(set(selected)) != len(selected) or any(name not in names for name in selected):
        parser.error("select unique catalog names or --all")
    results = []
    for name in selected:
        row = run_one(name, args)
        results.append(row)
        if row.get('unresolved_owned_cleanup'):
            print('Stopped before starting another template: owned cleanup needs recovery.', flush=True)
            break
    return int(any(not row["passed"] for row in results))


if __name__ == "__main__":
    raise SystemExit(main())
