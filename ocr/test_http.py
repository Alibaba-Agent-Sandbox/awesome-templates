"""Actual authentication/types/startup behavior, without a mock OCR acceptance."""
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
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));return sock.getsockname()[1]


@pytest.mark.parametrize('canonical',[False,True])
def test_real_http_auth_and_typed_contract_without_import_time_ocr(tmp_path,canonical):
    endpoint=port();token=secrets.token_hex(24);path=Path(__file__).with_name('commands.py')
    env={k:v for k,v in os.environ.items() if not any(word in k.upper() for word in ('KEY','TOKEN','SECRET','PASSWORD','CREDENTIAL'))}
    env.update(ABX_SERVER_TOKEN=token,ABX_SERVER_PORT=str(endpoint),ABX_PTY_PORT=str(port()),ABX_SERVER_BASE_DIR=str(tmp_path),WORKSPACE=str(tmp_path))
    argv=([sys.executable,'-m','agent_sandbox.server','serve','--commands',str(path),'--host','127.0.0.1','--port',str(endpoint)] if canonical else [sys.executable,str(path)])
    process=subprocess.Popen(argv,env=env,cwd=tmp_path,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        with httpx.Client(base_url=f'http://127.0.0.1:{endpoint}',headers={'Authorization':'Bearer '+token},timeout=5) as client:
            for _ in range(200):
                try:
                    if client.get('/health').status_code==200:break
                except httpx.HTTPError:pass
                time.sleep(.05)
            else:pytest.fail('canonical HTTP server failed to become healthy')
            assert httpx.get(str(client.base_url).rstrip('/')+'/commands').status_code==401
            assert {'ocr','ocr_version','ocr_setup_check','ocr_smoke'}<={row['name'] for row in client.get('/commands').json()['commands']}
            assert not list(tmp_path.glob('.ocr-*'))
            assert client.post('/commands/ocr',json={}).status_code==400
            response=client.post('/commands/ocr',json={'image_path':'/etc/synthetic-private-image.png'})
            assert response.status_code==500 and response.json()['type']=='ValueError'
            assert 'synthetic-private' not in response.text and token not in response.text
            assert client.post('/commands/nonexistent',json={}).status_code==404
    finally:
        process.terminate()
        try:process.wait(timeout=5)
        except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
