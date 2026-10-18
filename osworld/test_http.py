"""Actual authenticated HTTP contract in both supported startup forms, no fake GUI."""
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time

import httpx
import pytest


def port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));return sock.getsockname()[1]


@pytest.mark.parametrize('canonical',[False,True])
def test_authenticated_typed_protocol_and_no_import_time_desktop(tmp_path,canonical):
    endpoint=port();token=secrets.token_hex(20)
    path=Path(__file__).with_name('commands.py')
    env={k:v for k,v in os.environ.items() if not any(w in k.upper() for w in ['KEY','TOKEN','SECRET','PASSWORD','CREDENTIAL'])}
    env.update(ABX_SERVER_PORT=str(endpoint),ABX_PTY_PORT=str(port()),ABX_SERVER_TOKEN=token,ABX_SERVER_BASE_DIR=str(tmp_path),WORKSPACE=str(tmp_path))
    argv=([sys.executable,'-m','agent_sandbox.server','serve','--commands',str(path),'--host','127.0.0.1','--port',str(endpoint)] if canonical else [sys.executable,str(path)])
    process=subprocess.Popen(argv,env=env,cwd=tmp_path,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        with httpx.Client(base_url=f'http://127.0.0.1:{endpoint}',headers={'Authorization':'Bearer '+token},timeout=5) as client:
            deadline=time.monotonic()+15
            while time.monotonic()<deadline:
                try:
                    if client.get('/health').status_code==200:break
                except httpx.TransportError:pass
                time.sleep(.05)
            else:pytest.fail('HTTP server failed to become healthy')
            assert httpx.get(str(client.base_url).rstrip('/')+'/commands',timeout=5).status_code==401
            listing=client.get('/commands').json()['commands']
            names={x['name'] for x in listing}
            assert {'screenshot','click','type','hotkey','a11y_tree','run_task_config','evaluate'}<=names
            assert client.post('/commands/osworld_setup_check',json={}).json()['result']['running'] is False
            for name,payload in [('click',{'x':'invalid','y':3}),('type',{}),('hotkey',{})]:
                response=client.post('/commands/'+name,json=payload)
                assert response.status_code==400 and token not in response.text
            private='synthetic-private-task-path'
            response=client.post('/commands/run_task_config',json={'task_path':private})
            assert response.status_code==500 and response.json()['type']=='ValueError' and private not in response.text
            assert client.post('/commands/desktop_stop',json={}).json()=={'result':'stopped'}
            response=client.post('/commands/type',json={'text':'synthetic\x00invalid'})
            assert response.status_code==500 and response.json()['type']=='ValueError'
    finally:
        process.terminate()
        try:process.wait(timeout=5)
        except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
