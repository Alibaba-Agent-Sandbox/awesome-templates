"""Authored source boundaries and owned artifact/lifecycle control, no fake GUI pass."""
import base64,importlib.util,json,os,sys,tempfile
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('chrome_boundary_tests',Path(__file__).with_name('commands.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)


@pytest.mark.parametrize('url',['','file:///etc/passwd','https://user:pass@remote.invalid','https://@remote.invalid','http://remote.invalid:bad','http://remote.invalid/ a','x'*2049])
def test_invalid_open_never_reaches_native_worker(monkeypatch,url):
    monkeypatch.setattr(c,'request',lambda*a,**k:pytest.fail('invalid input reached browser'))
    with pytest.raises(ValueError):c.chrome_open(url)


def test_child_environment_excludes_operator_secrets_and_binary_overrides(tmp_path,monkeypatch):
    for key in ['OPENAI_API_KEY','GITHUB_TOKEN','ALICLOUD_ACCESS_KEY_SECRET','CHROME_BINARY','DISPLAY','ABX_SERVER_TOKEN']:
        monkeypatch.setenv(key,'unrelated-operator-value')
    value=c.environment(tmp_path)
    assert not any(key in value for key in ['OPENAI_API_KEY','GITHUB_TOKEN','ALICLOUD_ACCESS_KEY_SECRET','CHROME_BINARY','DISPLAY','ABX_SERVER_TOKEN'])
    assert value['HOME']==str(tmp_path)and value['TMPDIR']==str(tmp_path)


def test_screenshot_uses_exclusive_owned_path_and_real_byte_metadata(tmp_path,monkeypatch):
    from PIL import Image
    import io,hashlib
    output=io.BytesIO();Image.new('RGB',(4,3),(12,34,56)).save(output,format='PNG');raw=output.getvalue()
    monkeypatch.setattr(c,'ROOT',tmp_path)
    monkeypatch.setattr(c,'request',lambda*a,**k:{'content_base64':base64.b64encode(raw).decode(),'width':4,'height':3})
    first=c.chrome_screenshot();second=c.chrome_screenshot()
    assert first['path']!=second['path']
    assert Path(first['path']).read_bytes()==raw and Path(first['path']).stat().st_mode&0o777==0o600
    assert first['bytes']==len(raw)and first['sha256']==hashlib.sha256(raw).hexdigest()


def test_invalid_native_png_cannot_be_published(tmp_path,monkeypatch):
    monkeypatch.setattr(c,'ROOT',tmp_path)
    monkeypatch.setattr(c,'request',lambda*a,**k:{'content_base64':base64.b64encode(b'not a PNG').decode(),'width':4,'height':3})
    with pytest.raises(RuntimeError):c.chrome_screenshot()
    assert not list(tmp_path.iterdir())


def test_smoke_refuses_to_stop_an_existing_caller_session(monkeypatch):
    monkeypatch.setattr(c,'alive',lambda:True)
    monkeypatch.setattr(c,'chrome_stop',lambda:pytest.fail('caller session must remain'))
    with pytest.raises(RuntimeError,match='active caller'):c.chrome_smoke()


@pytest.mark.parametrize('result',[{'error':True,'stage':'native_browser','error_type':'RuntimeError'},{}])
def test_actual_ipc_failure_cleans_only_owned_worker(tmp_path,monkeypatch,result):
    import subprocess,threading
    private=tempfile.TemporaryDirectory(prefix='authored-chrome-ipc-');root=Path(private.name)
    worker=root/'worker.py';worker.write_text('import json\nprint('+repr(json.dumps(result))+',flush=True)\n')
    process=subprocess.Popen([sys.executable,str(worker)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,stdin=subprocess.PIPE,start_new_session=True,
        env={'PATH':'/usr/local/bin:/usr/bin:/bin','ABX_CHROME_OWNER':'synthetic-owner-marker'})
    reader=threading.Thread(target=lambda:process.stderr.read(),daemon=True);reader.start()
    c.PROCESS=process;c.PRIVATE=private;c.BUFFER=b''
    c.LIFE._STATE.update(process=process,private=private,reader=reader,port=0,owner='synthetic-owner-marker',pidfds={})
    monkeypatch.setattr(c,'ports_absent',lambda:True)
    with pytest.raises((RuntimeError,KeyError)):c.response(10)
    assert c.PROCESS is None and c.PRIVATE is None and not root.exists()


def test_readonly_setup_does_not_start_native(monkeypatch):
    monkeypatch.setattr(c,'alive',lambda:False)
    monkeypatch.setattr(c,'ports_absent',lambda:True)
    monkeypatch.setattr(c.subprocess,'Popen',lambda*a,**k:pytest.fail('inspection started a process'))
    assert c.chrome_setup_check()['mode']=='native-headed-cdp-vnc'
