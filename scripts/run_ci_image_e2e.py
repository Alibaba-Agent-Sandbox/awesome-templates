#!/usr/bin/env python3
"""Accept a verified CI image on Express, including owned registry cleanup.

Requires the native CLI, reviewed SDK, a verified crane binary and existing
account credentials in the process environment. Credentials never enter CI.
"""
from __future__ import annotations
import argparse
import ast
import importlib.util
import importlib.metadata
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
import secrets
import shlex
import time
import yaml
from public_launch_e2e import CLI, CLIError, require, matches, command_url, application_headers, delete_sandbox, json_contains, verify_cli_io
import ci_image_archive as images
from template_http_acceptance import fixture_environment, run_controller


def controller_missing_imports(source: Path) -> list[str]:
    pending=[source/'e2e_test.py'];seen=set();missing=set()
    while pending:
        path=pending.pop()
        if path in seen:continue
        seen.add(path);tree=ast.parse(path.read_text());names=set()
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):names.update(alias.name.split('.')[0] for alias in node.names)
            elif isinstance(node,ast.ImportFrom) and not node.level and node.module:names.add(node.module.split('.')[0])
        for name in names:
            peer=source/(name+'.py')
            if peer.is_file():pending.append(peer)
            elif importlib.util.find_spec(name) is None:missing.add(name)
    return sorted(missing)


def check_image_cli() -> None:
    """Reject a missing/renamed CLI surface before archive transfer or cloud writes."""
    result=CLI(os.environ.get('ABX','abx'),'alicloud-express',os.environ.copy()).run(
        ['template','from-image','--help'],30,native=True,json_output=False)
    required=['--generation','--start-cmd','--ready-cmd','--cpu','--memory',
              '--no-envd-inject','--registry-type','--registry-username','--registry-password']
    if any(flag not in result for flag in required):
        raise RuntimeError('CLI lacks the native template from-image contract; update ABX before image acceptance')


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


def prepared_launch_manifest(source: Path, template_id: str, *, runtime_env: dict[str, str] | None = None) -> dict:
    """Keep original launch declarations; apply prepared ENV defaults and its owned ID."""
    manifest=yaml.safe_load((source/'template.yaml').read_text())
    if runtime_env:
        manifest['env']={**runtime_env, **manifest.get('env', {})}
        assignments=' '.join(shlex.quote(key+'='+value) for key,value in manifest['env'].items() if value)
        if assignments:
            for key in ['start_cmd','ready_cmd']:
                if manifest.get(key):
                    manifest[key]='/usr/bin/env -- '+assignments+' /bin/sh -c '+shlex.quote(manifest[key])
    manifest.update(template_id=template_id,provider='alicloud-express')
    manifest.pop('image',None)
    return manifest


def exact_templates(cli: CLI, alias: str) -> list[str]:
    rows=cli.run(['template','list'],native=True)
    require(isinstance(rows,list),'native template inventory shape')
    return [row['TemplateID'] for row in rows if row.get('Name')==alias]


def delete_owned_templates(cli: CLI, alias: str, known_id: str | None, timeout: float=60) -> bool:
    """Delete exact owned IDs and require per-ID GetTemplate 404 plus empty alias."""
    ids=set(exact_templates(cli,alias))
    if known_id:ids.add(known_id)
    if not ids:return False  # An ambiguous submission cannot be cleared by an empty index.
    for identifier in ids:
        try:cli.run(['template','info',identifier],native=True)
        except CLIError as exc:
            if exc.diagnostics.get('code')=='E2001':continue
            raise
        cli.run(['template','delete',identifier,'--yes'],native=True,json_output=False)
    deadline=time.monotonic()+timeout
    for identifier in ids:
        while True:
            try:cli.run(['template','info',identifier],native=True)
            except CLIError as exc:
                if exc.diagnostics.get('code')=='E2001':
                    break
                raise
            if time.monotonic()>=deadline:return False
            time.sleep(1)
    return not exact_templates(cli,alias)


def wait_ready(cli: CLI, template_id: str, timeout: int=900) -> None:
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        value=cli.run(['template','info',template_id],native=True)
        state=value.get('status',value.get('Status'))
        if isinstance(state,dict):state=state.get('state')
        require(isinstance(state,str),'native readiness state shape')
        state=state.lower()
        if state=='ready':return
        require(state in {'submitted','pending','building','creating','initializing','processing'},'native image registration readiness')
        time.sleep(2)
    raise TimeoutError('owned image registration readiness timed out')


async def exercise(source: Path, template_id: str, private: Path, report: dict, http: bool, journal_path: Path,
                   *, runtime_env: dict[str, str] | None = None) -> None:
    from agent_sandbox import ProviderSandbox
    from agent_sandbox.models.errors import SandboxNotFoundError
    import httpx
    manifest=prepared_launch_manifest(source,template_id,runtime_env=runtime_env)
    runtime=private/'prepared-template';runtime.mkdir()
    (runtime/'template.yaml').write_text(yaml.safe_dump(manifest,sort_keys=False))
    environment=os.environ.copy()
    for key,value in manifest.get('env',{}).items():
        if value=='':environment.pop(key,None)
    environment['ABX_SERVER_TOKEN']=secrets.token_urlsafe(32)
    server_fixture,controller_fixture,fixture_proof=fixture_environment(source.name)
    environment.update(server_fixture)
    # Empty fixture declarations must be visible to the shared launch environment resolver.
    manifest.setdefault('env',{}).update({key:'' for key in server_fixture})
    (runtime/'template.yaml').write_text(yaml.safe_dump(manifest,sort_keys=False))
    cli=CLI(os.environ.get('ABX','abx'),'alicloud-express',environment)
    alias='image-app-'+uuid.uuid4().hex[:16]
    report.update(test_configuration=fixture_proof,sandbox_create='abx template launch',
        cli_version=cli.run(['--version'],json_output=False),client_version=importlib.metadata.version('agent-sandbox-client'),
        cli_distribution=os.environ.get('PUBLIC_LAUNCH_DISTRIBUTION','published'),cli_source_ref=os.environ.get('PUBLIC_LAUNCH_CLI_REF'),
        prepared_launch_manifest_sha256=hashlib.sha256((runtime/'template.yaml').read_bytes()).hexdigest())
    journals=cli.journal_directory
    before=set(journals.glob('*.json'));launch=None;sandbox=None;client=None
    try:
        launch=await asyncio.to_thread(cli.run,['template','launch',str(runtime),'--alias',alias,
            '--timeout','120','--sandbox-timeout','1200','--yes'],420)
        journal=json.loads(journal_path.read_text());journal['sandbox_ids']=[launch['sandbox_id']];images.save_private(journal_path,journal)
        sandbox=await ProviderSandbox.connect(launch['sandbox_id'],provider='alicloud-express')
        client=await sandbox.application_client(9000,token=environment['ABX_SERVER_TOKEN'])
        url,gateway_headers=await sandbox.network.resolve(9000)
        headers=application_headers(gateway_headers,environment['ABX_SERVER_TOKEN'])
        commands=[]
        report['commands']=commands
        async with httpx.AsyncClient(timeout=180) as remote:
            for index,case in enumerate(manifest['smoke']):
                name,args=case['command'],case.get('args',{})
                cli_result=await asyncio.to_thread(cli.run,['run',sandbox.id,name,'--json-args',json.dumps(args)])
                sdk_result=await client.commands.run(name,**args)
                response=await remote.post(command_url(url,name),headers=headers,json=args)
                require(response.status_code==200,'prepared image HTTP command')
                for via,result in [('cli',cli_result['result']),('sdk',sdk_result),('host-http',response.json()['result'])]:
                    require(matches(result,case['expect']) if 'expect' in case else result is not None and result!='',via+' manifest command result')
                    commands.append({'index':index,'name':name,'via':via,'ok':True,
                        'args_sha256':hashlib.sha256(json.dumps(args,sort_keys=True,separators=(',',':')).encode()).hexdigest()})
            response=await remote.post(command_url(url,manifest['smoke'][0]['command']),
                headers=application_headers(gateway_headers,'intentionally-wrong'),json=manifest['smoke'][0].get('args',{}))
            require(response.status_code==401,'actual startup service rejects wrong application token')
        require((await sandbox.files.read('/home/user/app/commands.py')).encode()==(source/'commands.py').read_bytes(),'actual runtime command bytes match source')
        result=await sandbox.commands.run('python3 -c "print(21*2)"',timeout=30)
        require(result.exit_code==0 and result.stdout.strip()=='42','SDK exec result')
        filename='/tmp/'+alias+'.txt';await sandbox.files.write(filename,'owned acceptance file\n')
        require(await sandbox.files.read(filename)=='owned acceptance file\n','SDK file readback')
        await sandbox.files.remove(filename);require(not await sandbox.files.exists(filename),'SDK file deletion')
        from server_package import server_version
        installed = await sandbox.commands.run('python3 -c "import importlib.metadata; print(importlib.metadata.version(\'agent-sandbox-server\'))"', timeout=30)
        require(installed.exit_code == 0 and installed.stdout.strip() == server_version(source),
                'actual prepared runtime server matches declared public package')
        report['server_package_version'] = installed.stdout.strip()
        await verify_cli_io(cli, sandbox, alias, private)
        report['commands']=commands
        report['checks']=['current unified launch starts original declared services','CLI/SDK/host HTTP manifest smoke',
            'actual startup service rejects wrong application token','actual runtime command bytes match source','SDK exec and file round trip','CLI exec/stat/upload/download and independent SDK byte/cleanup checks']
        if http:
            urls={};common_headers=None
            for port in manifest.get('ports',[9000]):
                endpoint,port_headers=await sandbox.network.resolve(port)
                require(common_headers is None or port_headers==common_headers,'same gateway authentication for declared services')
                common_headers=port_headers;urls[port]=endpoint
            report['http_acceptance']=await asyncio.to_thread(run_controller,source,urls,private,controller_fixture,
                token=environment['ABX_SERVER_TOKEN'],gateway_headers=common_headers)
            require(report['http_acceptance']['passed'],'complete current external HTTP controller')
        report['application_result']='PASS'
    finally:
        owned=set()
        uncertain=False
        for path in set(journals.glob('*.json'))-before:
            data=json.loads(path.read_text())
            if data.get('provider')!='alicloud-express':continue
            entries=data.get('entries',[])
            if not any(alias+'-' in str(entry.get('correlation_key','')) for entry in entries):continue
            for entry in entries:
                if entry['kind']=='sandbox':
                    if entry.get('id'):owned.add(entry['id'])
                    elif entry.get('state')!='deleted':uncertain=True
        if launch:owned.add(launch['sandbox_id'])
        cleanup=True
        for sid in owned:
            try:await delete_sandbox(ProviderSandbox,sid,'alicloud-express',SandboxNotFoundError)
            except Exception:cleanup=False
        report['cleanup_verified']=cleanup and bool(owned) and not uncertain
        report['uncertain_sandbox_intent']=uncertain
        for resource,method in [(client,'aclose'),(sandbox,'close')]:
            if resource is not None:
                try:await getattr(resource,method)()
                except Exception as failure:
                    report.setdefault('local_close_errors',[]).append(type(failure).__name__)


def run(source: Path,artifact_id: int,crane: str,*,http: bool=True,private_root: Path | None=None) -> int:
    source=source.resolve()
    if private_root is not None:
        private_root=private_root.resolve()
        if private_root.is_relative_to(source.parent):raise ValueError('private staging must stay outside the source checkout')
        private_root.mkdir(parents=True,exist_ok=True,mode=0o700)
    private=Path(tempfile.mkdtemp(prefix='abx-ci-image-',dir=private_root));private.chmod(0o700)
    journal_path=private/'registry-intent.json';platform_path=private/'platform-intent.json'
    registry_clean=False;template_clean=False
    report={'template':source.name,'provider':'alicloud-express','build_mode':'image',
        'verification_type':'ci-image-backed-external-http' if http else 'ci-image-backed-smoke','passed':False,'registry_cleanup_verified':False,
        'model_acceptance':'NOT_RUN','runtime_attempted':False,'cleanup_verified':False}
    alias='e2e-image-'+source.name[:24]+'-'+uuid.uuid4().hex[:8]
    cli=CLI(os.environ.get('ABX','abx'),'alicloud-express',os.environ.copy())
    try:
        missing=controller_missing_imports(source) if http else []
        if missing:
            report['missing_controller_modules']=missing
            raise RuntimeError('controller prerequisites missing before artifact or cloud operation')
        check_image_cli()
        print(source.name+': verifying exact-source CI image archive',flush=True)
        stage=private/'archive'
        images.download_verified(artifact_id,source,stage)
        if (stage/'public-package-origin.json').exists():report['image_build_origin']=json.loads((stage/'public-package-origin.json').read_text())
        print(source.name+': transferring verified image to owned private registry',flush=True)
        image_ref,proof,_=images.push_verified(stage,source,crane,journal_path)
        require(not exact_templates(cli,alias),'unique native registration alias preflight')
        images.save_private(platform_path,{'alias':alias,'preflight_absent':True,'registration_attempted':True,'sandbox_ids':[]})
        username,password=images.temporary_registry_credentials()
        resources=yaml.safe_load((source/'template.yaml').read_text()).get('resources',{})
        # Registration does not prestart an anonymous application: the shared launch core owns startup and runtime env.
        registered=cli.run(['template','from-image',image_ref,'--name',alias,'--generation','2',
            '--cpu',str(resources.get('cpu',2)),'--memory',str(resources.get('memory',2048)),
            '--no-envd-inject','--registry-type','acr','--registry-username='+username,'--registry-password='+password],native=True)
        template_id=registered['TemplateID'];journal=json.loads(platform_path.read_text())
        journal['template_id']=template_id;images.save_private(platform_path,journal)
        wait_ready(cli,template_id)
        report['runtime_attempted']=True
        print(source.name+': current CLI launch, SDK and full HTTP service verification',flush=True)
        asyncio.run(exercise(source,template_id,private,report,http,platform_path))
        final_digest=images.crane_call(crane,['digest',image_ref],username,password,90)
        require(final_digest==proof['pushed_image_digest'],'owned image tag digest after runtime')
        proof['tag_digest_verified_after_runtime']=True;report['image_provenance']=proof
    except Exception as exc:
        report['failure_type']=type(exc).__name__
        from public_launch_e2e import safe_failure_label,safe_diagnostics
        report['diagnostics']=safe_diagnostics(exc)
        if safe_failure_label(exc):report['failed_check']=safe_failure_label(exc)
    finally:
        if platform_path.exists():
            try:
                intent=json.loads(platform_path.read_text())
                template_clean=delete_owned_templates(cli,alias,intent.get('template_id'))
                intent['template_cleanup_verified']=template_clean;images.save_private(platform_path,intent)
            except Exception as exc:report['template_cleanup_failure_type']=type(exc).__name__
        if journal_path.exists():
            try:registry_clean=images.owned_registry_cleanup(json.loads(journal_path.read_text()),journal_path)
            except Exception as exc:report['registry_cleanup_error_type']=type(exc).__name__
        report.update(registry_cleanup_verified=registry_clean,template_cleanup_verified=template_clean)
        report['passed']=report.get('application_result')=='PASS' and report.get('cleanup_verified') is True and template_clean and registry_clean and not report.get('local_close_errors') and report.get('image_provenance',{}).get('tag_digest_verified_after_runtime') is True and (not http or report.get('http_acceptance',{}).get('passed') is True)
        report['result']='PASS' if report['passed'] else 'FAIL';images.save_private(private/'result.json',report)
    if report['passed']:
        manifest=yaml.safe_load((source/'template.yaml').read_text())
        receipt={**report,'template_version':str(manifest['version'])}
        publish(source,receipt,report);shutil.rmtree(private)
    else:
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
    parser.add_argument('--private-root',type=Path,help='Private archive/recovery staging outside the source checkout; RAM auth remains in the native temporary filesystem')
    args=parser.parse_args()
    return run(args.template,args.artifact_id,args.crane,http=True,private_root=args.private_root)

if __name__=='__main__':raise SystemExit(main())
