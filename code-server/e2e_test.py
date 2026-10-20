"""Real authenticated code-server lifecycle through the command and UI endpoints."""
import os
import secrets
import httpx


def main():
    token=os.environ.get('E2E_TOKEN','')
    headers={'Authorization':'Bearer '+token} if token else {}
    base=os.environ.get('E2E_BASE_URL','http://localhost:9000')
    web=os.environ.get('E2E_CODE_SERVER_URL','http://127.0.0.1:8443')
    with httpx.Client(base_url=base,headers=headers,timeout=180) as client:
        assert client.get('/health').status_code==200
        result=client.post('/commands/code_server_version',json={})
        assert result.status_code==200 and result.json()['result']=='4.141.0'
        result=client.post('/commands/code_server_self_test',json={})
        assert result.status_code==200 and result.json()['result']=='CODE_SERVER_OK'
        print('[PASS] installed pin and real wrong-password/login/workbench/cleanup self-test')
        password=secrets.token_urlsafe(24)
        started=False
        try:
            result=client.post('/commands/code_server_start',json={'password':password})
            assert result.status_code==200 and result.json()['result']=={'port':8443,'running':True,'auth':'password'}
            started=True
            result=client.post('/commands/code_server_status',json={})
            assert result.status_code==200 and result.json()['result']['running'] is True
            print('[PASS] owned IDE starts and persists across HTTP calls')
            with httpx.Client(base_url=web,timeout=30,follow_redirects=False) as ui:
                response=ui.get('/')
                assert response.status_code==302 and 'login' in response.headers.get('location','')
                wrong=ui.post('/login',data={'password':'synthetic-wrong-password'})
                assert 'set-cookie' not in wrong.headers
                login=ui.post('/login',data={'password':password})
                assert login.status_code==302 and 'set-cookie' in login.headers
                page=ui.get('/',follow_redirects=True)
                assert page.status_code==200 and 'workbench' in page.text
                print('[PASS] external forwarded-port authentication and actual IDE document')
            missing=client.post('/commands/code_server_start',json={'password':'short'})
            assert missing.status_code>=400
            assert client.post('/commands/unknown_ide_command',json={}).status_code==404
            print('[PASS] invalid password and unknown-command rejection')
        finally:
            if started:
                result=client.post('/commands/code_server_stop',json={})
                assert result.status_code==200 and result.json()['result']=={'running':False}
                result=client.post('/commands/code_server_status',json={})
                assert result.status_code==200 and result.json()['result']=={'running':False}
                print('[PASS] owned IDE stopped with independent status')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
