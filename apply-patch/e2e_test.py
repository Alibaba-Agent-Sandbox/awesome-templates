"""Real native apply_patch over HTTP; exact bytes retrieved through files API."""
import base64
import os
import uuid
import httpx


def main():
    token=os.environ.get("E2E_TOKEN","")
    headers={"Authorization":"Bearer "+token} if token else {}
    workspace=os.environ.get("E2E_BASE_DIR","/home/user/app")
    with httpx.Client(base_url=os.environ.get("E2E_BASE_URL","http://localhost:9000"),headers=headers,timeout=90) as client:
        assert client.get('/health').status_code==200
        version=client.post('/commands/apply_patch_version',json={})
        assert version.status_code==200 and version.json()['result']=='codex-cli 0.162.1'
        result=client.post('/commands/apply_patch_smoke',json={})
        assert result.status_code==200 and result.json()['result']=='APPLY_PATCH_OK'
        print('[PASS] actual pinned binary and add/update/move/delete/literal-input smoke')
        name='patch-http-'+uuid.uuid4().hex+'.txt'
        try:
            patch='*** Begin Patch\n*** Add File: '+name+'\n+HTTP_PATCH_BYTES\n*** End Patch\n'
            result=client.post('/commands/apply_patch',json={'patch_text':patch})
            assert result.status_code==200 and result.json()['result']['exit_code']==0
            fetched=client.get('/files/download-stream',params={'path':workspace+'/'+name})
            assert fetched.status_code==200 and base64.b64decode(fetched.json()['content_base64'])==b'HTTP_PATCH_BYTES\n'
            print('[PASS] remote modified bytes retrieved through files API')
            malformed=client.post('/commands/apply_patch',json={'patch_text':'not a patch'})
            assert malformed.status_code==200 and malformed.json()['result']['exit_code']!=0
            print('[PASS] invalid upstream patch is a nonzero result')
            for body in [{},{'patch_text':'not a patch','unexpected':True}]:
                assert client.post('/commands/apply_patch',json=body).status_code==400
            assert client.post('/commands/unknown_patch_command',json={}).status_code==404
            escaped=client.post('/commands/apply_patch',json={'patch_text':'*** Begin Patch\n*** Add File: ../escape\n+no\n*** End Patch\n'})
            assert escaped.status_code>=400
            print('[PASS] missing/undeclared/unknown/path-escape rejection')
        finally:
            deleted=client.delete('/files',params={'path':workspace+'/'+name})
            assert deleted.status_code==200
            absent=client.get('/files/download-stream',params={'path':workspace+'/'+name})
            assert absent.status_code==404
            print('[PASS] owned remote proof file cleanup and absence')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
