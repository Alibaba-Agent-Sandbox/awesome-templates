import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time
import xml.etree.ElementTree as ET
import pytest

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import commands as c
from swe_process import run


def test_explicit_shell_permission_required_before_credentials():
    for value in [False, 1, 'true', None]:
        with pytest.raises(ValueError, match='allow_execution'):
            c.swe_run_agent('0' * 32, allow_execution=value)


@pytest.mark.parametrize('value', ['../owned', '', '/tmp/test', 'g'*32, 'a'*31, None, 4])
def test_opaque_run_paths_reject_traversal(value, tmp_path, monkeypatch):
    monkeypatch.setenv('WORKSPACE', str(tmp_path))
    with pytest.raises(ValueError):c._resolve(value)


def test_symlink_run_storage_refused(tmp_path, monkeypatch):
    monkeypatch.setenv('WORKSPACE', str(tmp_path));(tmp_path/'outside').mkdir();(tmp_path/'.swe-runs').symlink_to(tmp_path/'outside')
    with pytest.raises(RuntimeError, match='symlink'):c._root()


def test_same_run_concurrent_operation_refused(tmp_path, monkeypatch):
    monkeypatch.setenv('WORKSPACE', str(tmp_path));run_id='a'*32;(c._root()/run_id).mkdir()
    with c._locked(run_id):
        with pytest.raises(RuntimeError, match='another operation'):
            with c._locked(run_id):pass


def test_child_env_keeps_home_without_credentials(tmp_path, monkeypatch):
    original=os.environ.get('HOME');monkeypatch.setenv('SWE_API_KEY','synthetic-key');monkeypatch.setenv('E2B_API_KEY','synthetic-provider-key');monkeypatch.setenv('OPENAI_API_KEY','synthetic-model-key');monkeypatch.setenv('GIT_CONFIG_COUNT','1')
    env=c._environment();assert env.get('HOME')==original
    assert not any(k in env for k in ['SWE_API_KEY','E2B_API_KEY','OPENAI_API_KEY','GIT_CONFIG_COUNT'])
    code,out,err=run([sys.executable,'-c','import os;print(any(k.endswith("API_KEY") for k in os.environ))'],cwd=str(tmp_path),env=env,timeout=3)
    assert code==0 and out.strip()=='False'


def _xml(tmp_path, *, failure=False, skipped=False, omit=False, duplicate=False):
    root=ET.Element('testsuites');suite=ET.SubElement(root,'testsuite')
    for i,name in enumerate(c.MANIFEST['fail_to_pass']+c.MANIFEST['pass_to_pass']):
        if omit and i==0:continue
        path,method=name.split('::',1);case=ET.SubElement(suite,'testcase',classname=path[:-3].replace('/','.'),name=method)
        if i==0 and failure:ET.SubElement(case,'failure')
        if i==1 and skipped:ET.SubElement(case,'skipped')
    if duplicate:suite.append(ET.fromstring(ET.tostring(case)))
    p=tmp_path/'result.xml';ET.ElementTree(root).write(p);return p


def test_all_real_declared_nodeids_required(tmp_path):
    values=c._test_results(_xml(tmp_path));assert len(values)==60 and set(values.values())=={'passed'}
    with pytest.raises(RuntimeError,match='every declared'):c._test_results(_xml(tmp_path,omit=True))
    with pytest.raises(RuntimeError,match='duplicate'):c._test_results(_xml(tmp_path,duplicate=True))


def test_junit_failure_and_skip_not_false_green(tmp_path):
    values=c._test_results(_xml(tmp_path,failure=True,skipped=True));assert list(values.values()).count('failed')==1;assert list(values.values()).count('skipped')==1


def test_marker_alone_is_not_test_execution(tmp_path):
    p=tmp_path/'empty.xml';p.write_text('<testsuites/>')
    with pytest.raises(RuntimeError,match='every declared'):c._test_results(p)


def _assert_process_not_running(pid):
    status=Path(f'/proc/{pid}/stat'); deadline=time.monotonic()+1
    while True:
        try:
            state=status.read_text().split()[2]
        except FileNotFoundError:
            return
        if state=='Z':return
        if time.monotonic()>=deadline:pytest.fail('owned child is still running')
        time.sleep(.01)


@pytest.mark.parametrize('deadline', [False,True])
def test_process_leader_exit_and_timeout_cleanup_descendants(tmp_path,deadline):
    marker=tmp_path/'pid'
    source='import subprocess,time,pathlib; p=subprocess.Popen(["sleep","60"]);pathlib.Path('+repr(str(marker))+').write_text(str(p.pid));'+('time.sleep(60)' if deadline else '')
    if deadline:
        with pytest.raises(RuntimeError,match='deadline'):run([sys.executable,'-c',source],cwd=str(tmp_path),env=c._environment(),timeout=.4)
    else:
        assert run([sys.executable,'-c',source],cwd=str(tmp_path),env=c._environment(),timeout=3)[0]==0
    _assert_process_not_running(int(marker.read_text()))


def test_bounded_output_drains_without_deadlock(tmp_path):
    code,out,err=run([sys.executable,'-c','import sys;sys.stdout.write("x"*3000000);sys.stderr.write("y"*3000000)'],cwd=str(tmp_path),env=c._environment(),timeout=5)
    assert code==0 and len(out)==len(err)==2*1024*1024


def test_unknown_instance_does_not_download_or_create(tmp_path,monkeypatch):
    monkeypatch.setenv('WORKSPACE',str(tmp_path))
    with pytest.raises(ValueError,match='only'):c.swe_prepare('other')
    assert not list(tmp_path.iterdir())


def test_real_shell_action_observes_stdout_and_nonzero(tmp_path):
    from swe_process import action
    value=action("printf 'héllo\\n'; printf 'stderr\\n' >&2; exit 7",cwd=str(tmp_path),env=c._environment(),timeout=3)
    assert value['returncode']==7 and value['output']=='héllo\nstderr\n'


def test_real_shell_action_timeout_exits_cli_and_cleans_child(tmp_path):
    marker=tmp_path/'action-child'
    command='sleep 60 & echo $! > '+str(marker)+'; wait'
    source='from swe_process import action; action('+repr(command)+',cwd='+repr(str(tmp_path))+',env={},timeout=.2)'
    code,out,err=run([sys.executable,'-c',source],cwd=str(HERE),env=c._environment(),timeout=4)
    assert code!=0 and 'action deadline' in err
    _assert_process_not_running(int(marker.read_text()))


def test_real_shell_action_background_child_reaped_at_cli_exit(tmp_path):
    marker=tmp_path/'action-background'
    command='sleep 60 & echo $! > '+str(marker)+'; echo visible'
    source='from swe_process import action; print(action('+repr(command)+',cwd='+repr(str(tmp_path))+',env={},timeout=2)["returncode"])'
    code,out,err=run([sys.executable,'-c',source],cwd=str(HERE),env=c._environment(),timeout=4)
    assert code==0
    _assert_process_not_running(int(marker.read_text()))


def test_wrong_node_failure_with_same_counts_rejected():
    baseline={'failed':1,'passed':59,'errors':0,'skipped':0,
        'fail_to_pass':dict.fromkeys(c.MANIFEST['fail_to_pass'],'failed'),
        'pass_to_pass':dict.fromkeys(c.MANIFEST['pass_to_pass'],'passed')}
    assert c._valid_baseline(baseline)
    baseline['fail_to_pass'][c.MANIFEST['fail_to_pass'][0]]='passed'
    baseline['pass_to_pass'][c.MANIFEST['pass_to_pass'][0]]='failed'
    assert not c._valid_baseline(baseline)
