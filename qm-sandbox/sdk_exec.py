"""Bounded authored tool runner reached only through actual Agent Sandbox SDK."""
import importlib.util,json,os,sys,tempfile
from pathlib import Path


def run(root,command,deadline):
    root=Path(root).resolve(strict=True)
    if not root.is_dir()or root==Path('/') or not isinstance(command,str)or not command.strip()or len(command.encode())>32768 or '\0'in command:raise ValueError('invalid bounded native tool request')
    if type(deadline)is not int or not 1<=deadline<=120:raise ValueError('tool deadline must be1..120seconds')
    spec=importlib.util.spec_from_file_location('qm_sdk_owned_process',Path(__file__).with_name('tool_process.py'))
    process=importlib.util.module_from_spec(spec);spec.loader.exec_module(process)
    with tempfile.TemporaryDirectory(prefix='abx-qm-tool-home-')as home:
        env={'PATH':'/opt/node/current/bin:/usr/local/bin:/usr/bin:/bin','HOME':home,'TMPDIR':home,'XDG_CACHE_HOME':home+'/cache','LANG':'C.UTF-8','GIT_CONFIG_GLOBAL':'/dev/null','GIT_CONFIG_NOSYSTEM':'1'}
        try:
            code,out,err=process.run(['/bin/bash','-lc',command],cwd=root,env=env,timeout=deadline)
        except RuntimeError as exc:
            if str(exc)=='QM execution exceeded timeout_s; output omitted':return {'stdout':'','stderr':'native tool execution deadline reached','code':124,'timedOut':True}
            raise
    return {'stdout':out,'stderr':err,'code':code,'timedOut':False}


if __name__=='__main__':
    try:
        value=json.loads(sys.argv[1])
        print(json.dumps({'result':run(value['root'],value['command'],value['deadline'])},ensure_ascii=False))
    except Exception as exc:
        print(json.dumps({'error_type':type(exc).__name__}))
        raise SystemExit(1)
