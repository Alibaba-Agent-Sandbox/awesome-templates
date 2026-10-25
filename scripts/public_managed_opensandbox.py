#!/usr/bin/env python3
"""Use published tools for the native OpenSandbox catalog and explicit foreign IDs.

Requires a dedicated disposable real Docker-backed OpenSandbox already running.
The source-only recipes and native provider-owned identities are separate inputs.
"""
from __future__ import annotations
import argparse, asyncio, importlib.metadata, importlib.util, json, os, sys
from pathlib import Path

from public_launch_e2e import CLI, CLIError, CheckFailed, delete_sandbox, require, safe_diagnostics

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('native_interpreter_verifier', ROOT/'docs/managed/tests/opensandbox_live.py')
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


async def verify(args):
    from agent_sandbox import ProviderSandbox
    from agent_sandbox.models.errors import SandboxNotFoundError
    cli = CLI(args.abx, 'opensandbox', os.environ.copy())
    report = {'result': 'FAIL', 'provider': 'opensandbox', 'installation_channel': 'published-npm-and-pypi',
              'cli_version': cli.run(['--version'], json_output=False),
              'python_client_version': importlib.metadata.version('agent-sandbox-client'),
              'python_server_version': importlib.metadata.version('agent-sandbox-server'),
              'managed_catalog': [], 'native_interpreter': None,
              'scope': 'native OpenSandbox catalog launch, shell/files and real persistent interpreter; foreign provider identities explicitly rejected'}
    phase = 'foreign-provider-identities'
    try:
        baseline = native.docker_ids()
        for name, provider in [('base','alicloud-express'), ('code-interpreter-v1','alicloud-express'), ('desktop','e2b')]:
            sid = None
            try:
                result = await asyncio.to_thread(cli.run, ['template','launch',name,'--sandbox-timeout','180','--yes'])
                sid = result.get('sandbox_id')
                raise CheckFailed('foreign provider-owned template identity must be rejected')
            except CLIError as failure:
                require(failure.diagnostics == {'code': 'E8002', 'category': 'provider-mismatch'}, 'foreign provider identity must reject with template compatibility error')
                report['managed_catalog'].append({'name': name, 'declared_provider': provider,
                    'result': 'NOT_APPLICABLE', 'rejection_verified': True, 'diagnostics': failure.diagnostics})
            finally:
                if sid:
                    await delete_sandbox(ProviderSandbox, sid, 'opensandbox', SandboxNotFoundError)
            require(native.docker_ids() == baseline, 'foreign managed identity creates no Docker resources')
        phase = 'native-catalog-cli-launch'
        sid = None
        sb = None
        try:
            launch = await asyncio.to_thread(cli.run, ['template','launch','opensandbox-code-interpreter','--sandbox-timeout','300','--yes'])
            sid = launch['sandbox_id']
            require(launch['provider']=='opensandbox', 'native catalog selected provider')
            sb = await ProviderSandbox.connect(sid, provider='opensandbox')
            phase = 'native-cli-exec'
            result = await asyncio.to_thread(cli.run, ['exec',sid,'--','python3','-c','print(6*7)'], json_output=False)
            shape = {'exact_expected': result.strip()=='42', 'contains_expected_line': '42' in result.splitlines(), 'character_count': len(result)}
            try:
                structured=json.loads(result)
                shape['json_type']=type(structured).__name__
                if isinstance(structured,dict):
                    shape['json_keys']=[key for key in structured if key in {'stdout','stderr','exit_code','execution_time','result','pid'}]
                    shape['json_stdout_expected']=structured.get('stdout','').strip()=='42' if isinstance(structured.get('stdout'),str) else False
            except ValueError:pass
            report['cli_exec_shape']=shape
            require(result.strip()=='42', 'public CLI native exec expected result')
            phase = 'native-sdk-shell-files'
            result = await sb.commands.run("python3 -c 'print(6*7)'", timeout=30)
            require(result.exit_code==0 and result.stdout.strip()=='42', 'public SDK native shell expected result')
            path='/tmp/owned-public-native.txt'
            await sb.files.write(path,'owned-native-file\n')
            require(await sb.files.read(path)=='owned-native-file\n','native file readback')
            await sb.files.remove(path)
            require(not await sb.files.exists(path),'native file absence')
            report['managed_catalog'].append({'name':'opensandbox-code-interpreter','declared_provider':'opensandbox',
                'result':'PASS','checks':['default public catalog CLI launch','CLI exec 42','SDK shell 42','SDK file write/read/delete']})
        finally:
            if sid:
                await delete_sandbox(ProviderSandbox,sid,'opensandbox',SandboxNotFoundError)
            if sb:
                await sb.close()
            require(native.docker_ids()==baseline, 'native catalog sandbox independently absent in Docker')
            report['catalog_cleanup']='independently confirmed absent'
        phase = 'native-interpreter-business'
        runtime=native.image('opensandbox/code-interpreter:v1.1.0')
        # Reuse the unchanged original business assertions, with installed public
        # client and current provider, against this run's disposable real backend.
        native.RESULT={'provider':'opensandbox','template':'opensandbox-code-interpreter',
            'template_id':'opensandbox/code-interpreter:v1.1.0','checks':[],
            'native_interpreter_verified':False,'cleanup_verified':False}
        args.work.mkdir(parents=True,exist_ok=False,mode=0o700)
        await native.exercise(args.work,runtime['digest'],runtime['image_id'])
        report['native_interpreter']=native.RESULT
        report['images']={'interpreter':runtime,'execd':native.image(os.environ['OSB_EXECD_IMAGE'])}
        require(native.RESULT['native_interpreter_verified'] and native.RESULT['cleanup_verified'], 'actual native interpreter and independent cleanup')
        report['result']='PASS'
    except Exception as failure:
        report['failed_phase']=phase
        report['failure_type']=type(failure).__name__
        report['diagnostics']=safe_diagnostics(failure)
        if isinstance(failure, CheckFailed):report['failed_check']=str(failure)
        if native.RESULT.get('checks'):report['native_interpreter']=native.RESULT
    finally:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        with args.output.open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    return 0 if report['result']=='PASS' else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--abx',default='abx');parser.add_argument('--work',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists() or args.work.exists():parser.error('output and work must be fresh; preserve earlier attempts')
    return asyncio.run(verify(args))

if __name__=='__main__':raise SystemExit(main())
