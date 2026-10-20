"""Real SQL/Redis external HTTP acceptance with independently removed nonce data."""
import os
import secrets
import httpx


def main():
    base=os.environ.get('E2E_BASE_URL','http://127.0.0.1:9000');token=os.environ.get('E2E_TOKEN','')
    headers={'Authorization':'Bearer '+token} if token else {}
    with httpx.Client(base_url=base,headers=headers,timeout=240) as client:
        def call(name,args=None):
            response=client.post('/commands/'+name,json=args or {});assert response.status_code==200,(name,response.status_code);return response.json()['result']
        assert client.get('/health').status_code==200
        setup=call('services_setup_check')
        assert setup['pinned_postgres']=='17.11' and setup['pinned_redis']=='8.0.2'
        assert client.post('/commands/services_start',json={'password':'short'}).status_code==500
        assert client.post('/commands/services_sql',json={}).status_code==400
        assert client.post('/commands/missing_db_command',json={}).status_code==404
        print('[PASS] readonly setup flags and invalid/missing/unknown command controls')
        if not setup['installed'] or not setup['pinned_versions_match']:
            if os.environ.get('E2E_REQUIRE_DATABASES')=='1':raise AssertionError('actual pinned database engines required')
            print('[SKIP] actual database runtime unavailable; contract checks do not establish engine/provider acceptance')
            return 0
        assert call('services_versions')=={'postgres':'17.11','redis':'8.0.2'}
        print('[PASS] actual fixed database engines and health')
        assert call('services_self_test')=='POSTGRES_REDIS_OK'
        print('[PASS] real authenticated SQL/Redis restart persistence and owned self-test cleanup')
        name='abx_e2e_db_'+secrets.token_hex(6);password=secrets.token_urlsafe(24);created=False
        try:
            assert call('services_start',{'password':password,'data_dir':name})['running'];created=True
            assert call('services_sql',{'sql':'SELECT 19+23'})=='42'
            assert call('services_redis',{'action':'SET','key':'proof','value':'42'})=='OK'
            assert call('services_redis',{'action':'GET','key':'proof'})=='42'
            assert call('services_status')['running']
            print('[PASS] actual persistent SQL/Redis through separate HTTP commands')
            assert client.post('/commands/services_redis',json={'action':'CONFIG'}).status_code==500
            assert client.post('/commands/services_sql',json={}).status_code==400
            assert client.post('/commands/missing_db_command',json={}).status_code==404
            print('[PASS] administrative Redis, missing argument and unknown-command controls')
        finally:
            assert call('services_stop')=={'running':False}
            assert call('services_status')=={'running':False}
            if created:
                root=os.environ.get('E2E_BASE_DIR','/home/user/app').rstrip('/')
                assert client.delete('/files',params={'path':root+'/'+name}).status_code==200
                assert client.get('/files',params={'path':root+'/'+name+'/.abx-dev-services.json'}).status_code==404
            print('[PASS] owned processes/listeners and nonce data deletion/absence')
    return 0

if __name__=='__main__':raise SystemExit(main())
