"""Actual native upstream MCP/process/privacy fixtures; no model/provider claim."""
import importlib.util
import os
from pathlib import Path
import socket
import time

import pytest

spec=importlib.util.spec_from_file_location('test_browser_mcp',Path(__file__).with_name('mcp_runtime.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

@pytest.fixture(autouse=True)
def owned():
    yield
    m.stop()


def test_real_native_mcp_counter_screenshot_and_complete_cleanup():
    assert m.self_test()=='PLAYWRIGHT_MCP_OK'
    assert m.status()=={'running':False}
    with socket.socket() as probe:
        probe.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);probe.bind(('127.0.0.1',m.PORT))


def test_actual_native_environment_private_state_and_detached_browser_cleanup(monkeypatch):
    home=os.environ.get('HOME');monkeypatch.setenv('OPENAI_API_KEY','synthetic-not-for-browser');monkeypatch.setenv('ABX_SERVER_TOKEN','synthetic-not-for-native-mcp');monkeypatch.setenv('NODE_OPTIONS','--invalid-injected-option')
    assert m.start()['running']
    env=(Path('/proc')/str(m.life._STATE['process'].pid)/'environ').read_bytes()
    assert b'synthetic-not-for' not in env and b'NODE_OPTIONS=' not in env
    result=m.call('tools/list');assert len(result['tools'])==25
    import json
    result=m.call('tools/call',json.dumps({'name':'browser_navigate','arguments':{'url':'data:text/html,<title>owned</title><p>browser</p>'}}))
    assert not result.get('isError')
    m.life._capture_owned();fds=list(m.life._STATE['pidfds']);assert len(fds)>1
    root=Path(m.life._STATE['private'].name);assert root.is_dir()
    m.stop();assert not root.exists() and os.environ.get('HOME')==home
    for pid in fds:
        try:state=Path('/proc',str(pid),'stat').read_text().split()[2]
        except FileNotFoundError:state='absent'
        assert state in ('absent','Z')


def test_unrelated_listener_survives_start_refusal():
    with socket.socket() as listener:
        listener.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);listener.bind(('0.0.0.0',m.PORT));listener.listen()
        with pytest.raises(RuntimeError,match='already in use'):m.start()
        m.stop();assert m.life._listener_exists(m.PORT)


@pytest.mark.parametrize('method,params',[('initialize','{}'),('tools/call','[]'),('tools/call','not-json'),('ping','x'*65537)])
def test_invalid_rpc_refuses_without_starting_process(method,params):
    with pytest.raises(ValueError):m.call(method,params)
    assert not m.life._STATE
