import importlib.util
from pathlib import Path
import socket
import sys
import pytest
sys.path.insert(0,str(Path(__file__).parent))
spec=importlib.util.spec_from_file_location('next_app_commands',Path(__file__).with_name('commands.py'));commands=importlib.util.module_from_spec(spec);spec.loader.exec_module(commands)

@pytest.fixture(autouse=True)
def workspace(tmp_path,monkeypatch):
    monkeypatch.setenv('WORKSPACE',str(tmp_path));monkeypatch.setenv('NEXT_APP_TOOLCHAIN',str(Path(__file__).parent))
    yield tmp_path
    commands.dev_stop()

@pytest.mark.parametrize('kind,marker',[('next',b'ABX_NEXT_PREVIEW'),('vite',b'ABX_VITE_PREVIEW')])
def test_actual_pinned_server_request_edit_and_owned_cleanup(workspace,kind,marker,monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY","synthetic-not-for-preview")
    assert commands.toolchain_versions()=={'next':'16.4.2','react':'19.3.1','react-dom':'19.3.1','vite':'8.3.4'}
    commands.scaffold(kind=kind,path='demo');info=commands.dev_start(kind=kind,path='demo',timeout_s=120)
    assert commands.dev_status()['running'];assert isinstance(commands.dev_logs(),str)
    assert b'synthetic-not-for-preview' not in Path('/proc/'+str(commands.life._STATE['process'].pid)+'/environ').read_bytes()
    assert marker in commands.life._request(info['port'],'GET','/')[2]
    target=workspace/'demo'/('app/page.js' if kind=='next' else 'index.html')
    target.write_text(target.read_text().replace(marker.decode(),'ABX_PREVIEW_EDITED'))
    import time
    deadline=time.monotonic()+30
    while time.monotonic()<deadline:
        if b'ABX_PREVIEW_EDITED' in commands.life._request(info['port'],'GET','/',timeout=10)[2]:break
        time.sleep(.2)
    else:pytest.fail('actual edited page was not served')
    assert commands.dev_stop()=={'running':False};assert not commands.life._listener_exists(info['port'])
    assert target.exists()


def test_no_overwrite_or_symlink_escape(workspace):
    commands.scaffold('vite','demo');(workspace/'demo'/'important').write_bytes(b'keep')
    with pytest.raises(FileExistsError):commands.scaffold('vite','demo')
    assert (workspace/'demo'/'important').read_bytes()==b'keep'
    for path in ['../outside','/tmp/outside','nested/path']:
        with pytest.raises(ValueError):commands.scaffold('vite',path)
    (workspace/'link').symlink_to('/tmp',target_is_directory=True)
    with pytest.raises(ValueError):commands.scaffold('vite','link')


def test_unrelated_listener_is_preserved(workspace):
    commands.scaffold('vite','demo')
    with socket.socket() as listener:
        listener.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);listener.bind(('0.0.0.0',5173));listener.listen()
        with pytest.raises(RuntimeError,match='already in use'):commands.dev_start('vite','demo')
        assert commands.life._listener_exists(5173)
        commands.dev_stop();assert commands.life._listener_exists(5173)


def test_kind_deadline_and_log_bounds(workspace):
    for action in [lambda:commands.scaffold('other'),lambda:commands.dev_start(timeout_s=0),lambda:commands.dev_logs(9000)]:
        with pytest.raises(ValueError):action()


def test_self_test_preserves_existing_project_and_cleans_all_owned_files(workspace):
    (workspace/'caller-file').write_bytes(b'keep')
    assert commands.preview_self_test()=='NEXT_VITE_PREVIEW_OK'
    assert sorted(p.name for p in workspace.iterdir())==['caller-file']
    assert (workspace/'caller-file').read_bytes()==b'keep'
    assert commands.dev_status()=={'running':False}


def test_exact_vite_host_reaches_actual_native_process(workspace):
    commands.scaffold('vite','hosted')
    assert commands.dev_start('vite','hosted',allowed_host='Preview.Example.COM')['running']
    data=Path('/proc',str(commands.life._STATE['process'].pid),'environ').read_bytes()
    assert b'__VITE_ADDITIONAL_SERVER_ALLOWED_HOSTS=preview.example.com' in data.split(b'\0')
    assert b'ABX_VITE_PREVIEW' in commands.life._request(5173,'GET','/')[2]
    commands.dev_stop();assert not commands.life._listener_exists(5173)


@pytest.mark.parametrize('host',['*','.example.com','https://preview.example.com','preview.example.com:5173','user@example.com','a..example.com','good.example,evil.example'])
def test_invalid_preview_host_refused_before_start(workspace,host):
    with pytest.raises(ValueError,match='allowed_host'):commands.dev_start('vite','absent',allowed_host=host)
    assert not commands.life._STATE
    assert list(workspace.iterdir())==[]


def test_real_next_hmr_accepts_exact_loopback_origin_and_rejects_other_origin(workspace):
    import asyncio
    import aiohttp
    commands.scaffold('next','hmr-origin')
    commands.dev_start('next','hmr-origin')
    async def verify(origin, allowed):
        async with aiohttp.ClientSession()as client:
            try:
                async with client.ws_connect('http://127.0.0.1:3000/_next/hmr',headers={
                        'Origin':origin,'Host':'localhost:3000'},timeout=aiohttp.ClientWSTimeout(ws_receive=10))as ws:
                    message=await ws.receive()
                    assert (message.type==aiohttp.WSMsgType.TEXT)is allowed
            except aiohttp.WSServerHandshakeError as error:
                assert not allowed
    asyncio.run(verify('http://127.0.0.1:19001',True))
    asyncio.run(verify('http://unrelated.example.invalid',False))
    logs=commands.dev_logs()
    assert 'Blocked cross-origin request'in logs and 'unrelated.example.invalid'in logs
