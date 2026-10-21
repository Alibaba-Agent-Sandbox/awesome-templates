"""Named scalar API for the pinned original Devin CLI."""
import importlib.util,os
from pathlib import Path
from agent_sandbox.server import command,start

spec=importlib.util.spec_from_file_location('devin_native_runtime',Path(__file__).with_name('runtime.py'))
RUNTIME=importlib.util.module_from_spec(spec);spec.loader.exec_module(RUNTIME)

@command('devin_version',description='Original hash-pinned native Devin CLI version; no model call.')
def devin_version()->str:
    return RUNTIME.diagnostic(['--version'])

@command('devin_setup_check',description='Presence-only settings; no network or credential values.')
def devin_setup_check()->dict:
    return RUNTIME.setup()

@command('devin_native_check',description='Verify original file hashes and actual native headless flags; no model call.')
def devin_native_check()->dict:
    text=RUNTIME.diagnostic(['--help'])
    return {'original_native':True,'headless_print':'--print'in text,'private_config':'--config'in text,
            'explicit_permission':'--permission-mode'in text,'workspace_trust_control':'--respect-workspace-trust'in text}

@command('devin',description='Original Devin CLI with explicit disposable-sandbox tool permission; no credential fallback.')
def devin(prompt:str,cwd:str='',command_timeout:int=300,allow_unsafe_tools:bool=False,model:str='')->dict:
    return RUNTIME.run(prompt,cwd,command_timeout,allow_unsafe_tools,model)

if __name__=='__main__':start(int(os.environ.get('ABX_SERVER_PORT','9000')))
