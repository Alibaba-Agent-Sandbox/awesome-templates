"""Actual owned-process/browser regressions; no model or provider claim."""
import importlib.util
import json
import os
from pathlib import Path
import secrets
import signal
import sys
import pytest
spec=importlib.util.spec_from_file_location('pdf_browser_commands',Path(__file__).with_name('commands.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)


def test_failed_workspace_script_leaves_no_owned_background_child(tmp_path,monkeypatch):
    monkeypatch.setenv('WORKSPACE',str(tmp_path));nonce=secrets.token_hex(12);pidfile=tmp_path/'owned-child.pid'
    body='import os,subprocess,sys\nfrom pathlib import Path\np=subprocess.Popen([sys.executable,"-c","import time;time.sleep(60)"],env=dict(os.environ,ABX_PDF_TEST_OWNER='+repr(nonce)+'),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)\nPath('+repr(str(pidfile))+').write_text(str(p.pid))\nraise SystemExit(7)\n'
    (tmp_path/'failing.py').write_text(body)
    try:
        with pytest.raises(RuntimeError):c.run('failing.py',timeout_s=2)
        pid=int(pidfile.read_text())
        try:state=Path('/proc',str(pid),'stat').read_text().split()[2]
        except FileNotFoundError:state='absent'
        assert state in ('absent','Z')
    finally:
        if pidfile.exists():
            pid=int(pidfile.read_text());fd=None
            try:
                fd=os.pidfd_open(pid)
                if ('ABX_PDF_TEST_OWNER='+nonce).encode() in Path('/proc',str(pid),'environ').read_bytes().split(b'\0'):
                    signal.pidfd_send_signal(fd,signal.SIGKILL)
            except (FileNotFoundError,ProcessLookupError):pass
            finally:
                if fd is not None:os.close(fd)


@pytest.mark.parametrize('landscape',[False,True])
def test_actual_pdf_bytes_and_orientation(tmp_path,monkeypatch,landscape):
    import re
    monkeypatch.setenv('WORKSPACE',str(tmp_path))
    result=c.pdf('data:text/html,<h1>Real PDF proof</h1>',landscape=landscape)
    path=Path(result['path']);data=path.read_bytes()
    assert result['format']=='PDF' and result['bytes']==len(data)>1000
    assert data.startswith(b'%PDF-') and b'%%EOF' in data[-100:]
    match=re.search(rb'/MediaBox\s*\[\s*0\s+0\s+([\d.]+)\s+([\d.]+)',data);assert match
    width,height=map(float,match.groups());assert (width>height)==landscape
    path.unlink()


def test_render_symlink_directory_refused_without_writing(tmp_path,monkeypatch):
    monkeypatch.setenv('WORKSPACE',str(tmp_path));outside=tmp_path/'caller';outside.mkdir();(tmp_path/'browser-artifacts').symlink_to(outside,target_is_directory=True)
    with pytest.raises(ValueError,match='symlink'):c.pdf('data:text/html,proof')
    assert list(outside.iterdir())==[]


def test_actual_script_deadline_and_output_bound(tmp_path,monkeypatch):
    import time
    monkeypatch.setenv('WORKSPACE',str(tmp_path));(tmp_path/'slow.py').write_text('import time;time.sleep(60)')
    before=time.monotonic()
    with pytest.raises(RuntimeError,match='timeout_s'):c.run('slow.py',timeout_s=1)
    assert time.monotonic()-before<8
    (tmp_path/'noisy.py').write_text('import sys;sys.stderr.write("x"*1000000)')
    with pytest.raises(RuntimeError,match='256KiB'):c.run('noisy.py',timeout_s=2)


def test_native_script_child_excludes_server_and_cloud_secrets(tmp_path,monkeypatch):
    monkeypatch.setenv('WORKSPACE',str(tmp_path))
    keys=['OPENAI_API_KEY','ALICLOUD_ACCESS_KEY_ID','ABX_SERVER_TOKEN','GITHUB_TOKEN','NODE_OPTIONS']
    for key in keys:monkeypatch.setenv(key,'synthetic-not-for-script')
    (tmp_path/'env.py').write_text('import os;print(any(key in os.environ for key in '+repr(keys)+'))')
    assert c.run('env.py',timeout_s=2)=='False\n'
