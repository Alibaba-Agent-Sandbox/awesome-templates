"""Typed native K3s diagnostics and ephemeral manifest validation."""
import importlib.util,os
from pathlib import Path
from agent_sandbox.server import command,start
spec=importlib.util.spec_from_file_location('original_k3s_runtime',Path(__file__).with_name('runtime.py'))
RUNTIME=importlib.util.module_from_spec(spec);spec.loader.exec_module(RUNTIME)
@command('k3s_version',description='Original pinned binary identity and version; no cluster.')
def k3s_version()->str:return RUNTIME.diagnostic(['--version'])
@command('k3s_setup_check',description='Read-only local runtime presence/profile; no cluster or credentials.')
def k3s_setup_check()->dict:return RUNTIME.setup()
@command('k3s_native_check',description='Actual original server help; no cluster.')
def k3s_native_check()->dict:
    text=RUNTIME.diagnostic(['server','--help'])
    return {'original_native':True,'agentless_flag_in_help':'--disable-agent'in text,'private_data':'--data-dir'in text,'private_kubeconfig':'--write-kubeconfig'in text,'explicit_port':'--https-listen-port'in text}
@command('validate_manifest',description='Original ephemeral non-root agentless server and strict server-side dry-run; no nodes or Pod execution.')
def validate_manifest(manifest_yaml:str,command_timeout:int=180)->dict:return RUNTIME.validate(manifest_yaml,command_timeout)
if __name__=='__main__':start(int(os.environ.get('ABX_SERVER_PORT','9000')))
