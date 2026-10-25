"""Actual external HTTP runtime acceptance; each owned project is removed."""
import os
import secrets
import httpx

# The host runner passes provider gateway authentication separately from app auth.
import json as _e2e_json
_GATEWAY_HEADERS = _e2e_json.loads(os.environ.get("E2E_GATEWAY_HEADERS_JSON", "{}"))
if not isinstance(_GATEWAY_HEADERS, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in _GATEWAY_HEADERS.items()):
    raise ValueError("E2E_GATEWAY_HEADERS_JSON must be an object of string headers")
_APPLICATION_HEADERS = {"Authorization": "Bearer " + os.environ["ABX_SERVER_TOKEN"]} if os.environ.get("ABX_SERVER_TOKEN") else {}


def main():
    base=os.environ.get('E2E_BASE_URL','http://127.0.0.1:9000');token=os.environ.get('ABX_SERVER_TOKEN','')
    headers={'Authorization':'Bearer '+token} if token else {}
    with httpx.Client(base_url=base,headers={**(headers), **_GATEWAY_HEADERS, **_APPLICATION_HEADERS},timeout=200) as client:
        def run(name,args=None):
            result=client.post('/commands/'+name,json=args or {});assert result.status_code==200,(name,result.status_code);return result.json()['result']
        assert client.get('/health').status_code==200
        assert run('toolchain_versions')=={'next':'16.4.2','react':'19.3.1','react-dom':'19.3.1','vite':'8.3.4'}
        print('[PASS] actual installed framework pins and health')
        for kind in ['next','vite']:
            name='e2e-preview-'+secrets.token_hex(6);created=False;started=False
            try:
                assert run('scaffold',{'kind':kind,'path':name})=={'path':name,'kind':kind};created=True
                result=run('dev_start',{'kind':kind,'path':name});started=True
                assert result=={'port':3000 if kind=='next' else 5173,'kind':kind,'running':True}
                assert run('dev_status')['path']==name
                assert isinstance(run('dev_logs'),str)
                assert client.post('/commands/scaffold',json={'kind':kind,'path':name}).status_code==500
                print('[PASS] real '+kind+' server readiness, persistence and overwrite rejection')
            finally:
                if started:assert run('dev_stop')=={'running':False}
                assert run('dev_status')=={'running':False}
                if created:
                    # Use the image server files contract, confined to this nonce directory.
                    root=os.environ.get('E2E_BASE_DIR','/home/user/app').rstrip('/')
                    result=client.delete('/files',params={'path':root+'/'+name})
                    assert result.status_code==200
                    assert client.get('/files',params={'path':root+'/'+name+'/package.json'}).status_code==404
                print('[PASS] '+kind+' owned process/listener and project cleanup')
        assert client.post('/commands/scaffold',json={'path':'../outside'}).status_code==500
        assert client.post('/commands/missing_preview_command',json={}).status_code==404
        print('[PASS] path and unknown-command rejection')
    return 0

if __name__=='__main__':raise SystemExit(main())
