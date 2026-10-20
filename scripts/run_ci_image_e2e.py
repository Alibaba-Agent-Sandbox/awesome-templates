#!/usr/bin/env python3
"""Accept a verified CI image on Express, including owned registry cleanup.

Requires the native CLI, reviewed SDK, a verified crane binary and existing
account credentials in the process environment. Credentials never enter CI.
"""
from __future__ import annotations
import argparse
import ast
import importlib.util
import asyncio
import contextlib
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import uuid
import ci_image_archive as images
import express_e2e as harness


def controller_missing_imports(source: Path) -> list[str]:
    tree=ast.parse((source/'e2e_test.py').read_text());names=set()
    for node in ast.walk(tree):
        if isinstance(node,ast.Import):names.update(alias.name.split('.')[0] for alias in node.names)
        elif isinstance(node,ast.ImportFrom) and not node.level and node.module:names.add(node.module.split('.')[0])
    return sorted(name for name in names if not (source/(name+'.py')).exists() and importlib.util.find_spec(name) is None)


def publish(source: Path, receipt: dict, report: dict) -> None:
    """Never publish an acceptance receipt before all owned cleanup passes."""
    if not (report.get('passed') is True and report.get('registry_cleanup_verified') is True):
        raise ValueError('acceptance publication requires independently verified registry cleanup')
    if report.get('image_provenance',{}).get('tag_digest_verified_after_runtime') is not True:
        raise ValueError('acceptance requires registry tag digest readback after runtime')
    directory=source/'evidence';directory.mkdir(exist_ok=True)
    stamp=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H%M%SZ')
    receipt=dict(receipt,registry_cleanup_verified=True)
    canonical=directory/('express-'+stamp[:10]+'.json')
    if canonical.exists():canonical=directory/('express-'+stamp+'.json')
    # Exclusive creation preserves every earlier attempt/acceptance.
    with canonical.open('x') as stream:json.dump(receipt,stream,indent=2);stream.write('\n')
    with (directory/('image-http-'+stamp+'.json')).open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')


def run(source: Path,artifact_id: int,crane: str,*,http: bool=True) -> int:
    source=source.resolve();private=Path(tempfile.mkdtemp(prefix='abx-ci-image-'));private.chmod(0o700)
    journal_path=private/'registry-intent.json';status=1;registry_clean=False;checks={};receipt=None
    report={'template':source.name,'provider':'alicloud-express','build_mode':'image',
        'verification_type':'ci-image-backed-external-http','passed':False,'registry_cleanup_verified':False,
        'model_acceptance':'NOT_RUN','http_acceptance':checks}
    try:
        missing=controller_missing_imports(source) if http else []
        if missing:
            report['missing_controller_modules']=missing
            print('BLOCKED local HTTP controller prerequisites: '+', '.join(missing),flush=True)
            raise RuntimeError('controller prerequisites missing before artifact or cloud operation')
        print(source.name+': verifying exact-source CI image archive',flush=True)
        stage=private/'archive';images.download_verified(artifact_id,source,stage)
        print(source.name+': verified archive; transferring to owned private registry',flush=True)
        image_ref,proof,journal=images.push_verified(stage,source,crane,journal_path)
        # The identical public context is staged outside the checkout so the
        # harness can write a private provisional receipt without touching history.
        runtime=private/source.name
        shutil.copytree(source,runtime,ignore=shutil.ignore_patterns('evidence','__pycache__','*.pyc'))
        proof_path=private/'image-proof.json';proof_path.write_text(json.dumps(proof))
        options=harness.build_options([str(runtime),'--build','image','--image-ref',image_ref,'--image-proof',str(proof_path),
            '--alias','e2e-image-'+source.name+'-'+uuid.uuid4().hex[:8],'--timeout','900',
            '--wall-timeout','1200','--idle-timeout','600','--push-retries','0','--sandbox-timeout','1200'])
        username,password=images.temporary_registry_credentials()
        prior={key:os.environ.get(key) for key in ['ABX_IMAGE_REGISTRY_USERNAME','ABX_IMAGE_REGISTRY_PASSWORD','ABX_IMAGE_CRANE']}
        os.environ.update(ABX_IMAGE_REGISTRY_USERNAME=username,ABX_IMAGE_REGISTRY_PASSWORD=password,ABX_IMAGE_CRANE=crane)
        done=False
        async def endpoint(sid):
            from agent_sandbox.api.sandbox import Sandbox
            sandbox=await Sandbox.connect(sid)
            try:
                import yaml
                ports=yaml.safe_load((source/'template.yaml').read_text()).get('ports',[9000])
                return {port:sandbox.network.get_url(port) for port in ports}
            finally:await sandbox.close()
        def sdk(sid,command,args):
            nonlocal done
            result=harness.default_sdk(sid,command,args)
            if http and not done:
                done=True;urls=asyncio.run(endpoint(sid));base=urls[9000];script=source/'e2e_test.py'
                env={k:v for k,v in os.environ.items() if not any(x in k.upper() for x in ['TOKEN','API_KEY','SECRET','PASSWORD','ACCESS_KEY'])}
                env.update(E2E_BASE_URL=base,E2E_BASE_DIR='/home/user/app',E2E_WORKSPACE='/home/user/app',E2E_RUN_LLM='0',E2E_REQUIRE_CLI='1')
                if source.name=='code-server':env['E2E_CODE_SERVER_URL']=urls[8443]
                if source.name=='next-app':env.update(E2E_NEXT_URL=urls[3000],E2E_VITE_URL=urls[5173])
                result_http=harness.run_monitored([sys.executable,str(script)],env=env,idle_timeout=600,wall_timeout=600)
                (private/'http.log').write_text(result_http.stdout+'\n'+result_http.stderr)
                lines=(result_http.stdout+'\n'+result_http.stderr).splitlines()
                # Only count outcomes: assertion text may contain private URLs.
                checks.update(passed=result_http.returncode==0,exit_code=result_http.returncode,
                    pass_count=sum(x.startswith('[PASS]') for x in lines),fail_count=sum(x.startswith('[FAIL]') for x in lines),
                    skip_count=sum(x.startswith('[SKIP]') for x in lines),verifier_sha256=hashlib.sha256(script.read_bytes()).hexdigest())
                if result_http.returncode:raise RuntimeError('full external HTTP acceptance failed; private log retained')
            return result
        print(source.name+': actual native template create, READY and CLI/SDK verification',flush=True)
        try:
            with (private/'harness.log').open('w') as output,contextlib.redirect_stdout(output),contextlib.redirect_stderr(output):
                def verify_owned(intent,runner):
                    observed=harness.owned_resources_absent(intent,runner)
                    report['cleanup_verified']=observed
                    return observed
                status=harness.execute(options,sdk=sdk,verify=verify_owned)
        finally:
            for key,value in prior.items():
                if value is None:os.environ.pop(key,None)
                else:os.environ[key]=value
        final_digest=images.crane_call(crane,['digest',image_ref],username,password,90)
        if final_digest!=proof['pushed_image_digest']:raise ValueError('owned registry tag changed during acceptance')
        proof['tag_digest_verified_after_runtime']=True
        report.update(image_provenance=proof)
        report.setdefault('cleanup_verified',False)
        if status==0:
            receipt=json.loads(next((runtime/'evidence').glob('express-*.json')).read_text())
            receipt['image_provenance']=proof
    except Exception as exc:
        # Upstream exceptions can embed temporary signed locations or credentials.
        report['failure_type']=type(exc).__name__;status=1
    finally:
        if journal_path.exists():
            try:registry_clean=images.owned_registry_cleanup(json.loads(journal_path.read_text()),journal_path)
            except Exception as exc:report['registry_cleanup_error_type']=type(exc).__name__
        report['registry_cleanup_verified']=registry_clean
        report['passed']=status==0 and receipt is not None and registry_clean and (not http or checks.get('passed') is True)
        report['result']='PASS' if report['passed'] else 'FAIL'
        images.save_private(private/'result.json',report)
    if report['passed']:
        publish(source,receipt,report)
        shutil.rmtree(private)
    else:
        # The private recovery journal remains authoritative; never export it.
        print('Private attempt retained at '+str(private),flush=True)
        directory=source/'evidence';directory.mkdir(exist_ok=True)
        stamp=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H%M%SZ')
        with (directory/('image-attempt-'+stamp+'.json')).open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    print(source.name+': '+report['result']+'; registry cleanup='+str(registry_clean),flush=True)
    return 0 if report['passed'] else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('template',type=Path);parser.add_argument('--artifact-id',type=int,required=True)
    parser.add_argument('--crane',required=True,help='Path to verified upstream crane binary')
    parser.add_argument('--smoke-only',action='store_true',help='Explicitly omit full HTTP acceptance')
    args=parser.parse_args();return run(args.template,args.artifact_id,args.crane,http=not args.smoke_only)

if __name__=='__main__':raise SystemExit(main())
