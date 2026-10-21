"""Named scalar API for the pinned original Cursor Agent CLI."""
import importlib.util,os
from pathlib import Path
from agent_sandbox.server import command,start

spec=importlib.util.spec_from_file_location('cursor_native_runtime',Path(__file__).with_name('runtime.py'))
RUNTIME=importlib.util.module_from_spec(spec);spec.loader.exec_module(RUNTIME)

@command('agent_version',description='Original hash-pinned native Cursor CLI version; no model call.')
def agent_version()->str:
    return RUNTIME.diagnostic(['--version'])

@command('agent_setup_check',description='Presence-only settings; no network or credential values.')
def agent_setup_check()->dict:
    return RUNTIME.setup()

@command('agent_native_check',description='Verify original file hashes and actual native headless flags; no model call.')
def agent_native_check()->dict:
    text=RUNTIME.diagnostic(['--help'])
    return {'original_native':True,'headless_print':'--print'in text,'json_output':'--output-format'in text,
            'explicit_force':'--force'in text,'contained_workspace':'--workspace'in text}

@command('agent',description='Original Cursor CLI with explicit disposable-sandbox tool permission; no vendor-key fallback.')
def agent(prompt:str,cwd:str='',command_timeout:int=300,allow_unsafe_tools:bool=False,model:str='')->dict:
    return RUNTIME.run(prompt,cwd,command_timeout,allow_unsafe_tools,model)

if __name__=='__main__':start(int(os.environ.get('ABX_SERVER_PORT','9000')))
