"""Actual installed official mini CLI + deterministic upstream model controls.

No external model/network. This proves CLI-loop observation and fatal timeout
propagation, not real-model coding or benchmark results.
"""
import json
import os
from pathlib import Path
import tempfile
import commands as c
from swe_process import run


def message(command):
    return {'role':'assistant','content':'owned deterministic control','extra':{'actions':[{'command':command}],'cost':0}}


def invoke(root, name, outputs, timeout=1):
    folder=root/name;folder.mkdir(mode=0o700);trajectory=folder/'trajectory.json'
    config={'run':{'task':'owned deterministic adapter regression'},
        'agent':{'agent_class':'default','system_template':'Execute the provided task.','instance_template':'{{task}}','step_limit':4,'cost_limit':0,'output_path':str(trajectory)},
        'model':{'model_class':'deterministic','model_name':'deterministic','outputs':[message(command) for command in outputs]},
        'environment':{'environment_class':'swe_environment.OwnedLocalEnvironment','cwd':str(folder),'timeout':timeout,'env':{'PATH':'/usr/bin:/bin'}}}
    config_path=folder/'config.yaml';config_path.write_text(json.dumps(config));config_path.chmod(0o600)
    env=c._environment()|{'PYTHONPATH':str(c.HERE),'MSWEA_GLOBAL_CONFIG_DIR':str(folder/'config'),'MSWEA_CONFIGURED':'true','MSWEA_SILENT_STARTUP':'1'}
    code,out,err=run([c.MINI,'-c',str(config_path),'-o',str(trajectory)],cwd=str(folder),env=env,timeout=20)
    return code,json.loads(trajectory.read_text())


def main():
    with tempfile.TemporaryDirectory(prefix='swe-official-guards-') as temporary:
        root=Path(temporary)
        code,state=invoke(root,'observation',["printf 'héllo\\n'; printf 'stderr\\n' >&2; exit 7",'echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT'])
        assert code==0 and state['info']['exit_status']=='Submitted'
        observations=[m.get('content','') for m in state['messages'] if m.get('role')=='user']
        assert any('héllo' in m and 'stderr' in m and '<returncode>7</returncode>' in m for m in observations),'CLI lost actual action output/nonzero'
        print('PASS actual official CLI propagates Unicode stdout/stderr and nonzero action result',flush=True)
        pid_file=root/'child.pid';after=root/'must-not-run'
        code,state=invoke(root,'timeout',['sleep 60 & echo $! > '+str(pid_file)+'; wait','touch '+str(after)])
        assert code!=0 and state['info']['exit_status']=='RuntimeError' and state['info']['model_stats']['api_calls']==1,'CLI swallowed environment timeout and continued'
        assert not after.exists(),'CLI continued after fatal action timeout'
        pid=int(pid_file.read_text());stat=Path('/proc')/str(pid)/'stat'
        assert not stat.exists() or stat.read_text().split()[2]=='Z','ordinary action child survived owned CLI cleanup'
        print('PASS actual official CLI fatal action timeout stops loop and owned child is absent or exited',flush=True)
    return 0


if __name__=='__main__':raise SystemExit(main())
