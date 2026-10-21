"""Actual local HTTP with fixed non-executable replies and synthetic credentials."""
import contextlib,http.client,importlib.util,json,socket,threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import httpx,pytest
spec=importlib.util.spec_from_file_location('muse_relay_controls',Path(__file__).with_name('relay.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

@contextlib.contextmanager
def upstream(redirect=None):
    seen=[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            data=self.rfile.read(int(self.headers['Content-Length']));seen.append({'path':self.path,'authorization':self.headers.get('Authorization'),'body':data})
            if redirect:
                self.send_response(307);self.send_header('Location',redirect);self.end_headers();return
            data=b'event: response.completed\ndata: {"fixed":"non-executable"}\n\n'
            self.send_response(200);self.send_header('Content-Type','text/event-stream');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:yield 'http://127.0.0.1:'+str(server.server_port),seen
    finally:server.shutdown();server.server_close();thread.join(timeout=3)


def test_actual_relay_keeps_original_response_bytes_and_separate_credentials():
    with upstream()as(base,seen):
        relay=module.Relay(base+'/v1','UPSTREAM_SYNTHETIC_SECRET','unit-model',20)
        try:
            with httpx.Client(base_url=relay.url,headers={'Authorization':'Bearer '+relay.token})as client:
                value=client.get('/muse-code/models');assert value.status_code==200 and value.json()['data'][0]['id']=='unit-model';assert not seen
                raw=b'{"model":"unit-model", "stream":true,"tools":[],"input":"fixed non-executable"}'
                value=client.post('/responses',content=raw);assert value.status_code==200 and value.content==b'event: response.completed\ndata: {"fixed":"non-executable"}\n\n'
                relay.wait_for_idle();assert seen==[{'path':'/v1/responses','authorization':'Bearer UPSTREAM_SYNTHETIC_SECRET','body':raw}]
                assert relay.snapshot()['completed_responses']==1
        finally:relay.close()
        with socket.socket()as probe:
            probe.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);probe.bind(('127.0.0.1',relay.port))


def test_no_auth_path_or_model_bypass_can_reach_upstream():
    with upstream()as(base,seen):
        relay=module.Relay(base,'SYNTHETIC_SECRET','unit-model',20)
        try:
            with httpx.Client(base_url=relay.url)as client:
                assert client.get('/muse-code/models').status_code==403
                assert client.post('/responses',json={'model':'unit-model','stream':True}).status_code==403
                client.headers['Authorization']='Bearer '+relay.token
                assert client.get('/elsewhere').status_code==403
                assert client.post('/elsewhere',json={}).status_code==403
                for value in [{'model':'other','stream':True},{'model':'unit-model','stream':False},[],None]:assert client.post('/responses',content=json.dumps(value)).status_code==400
                with socket.create_connection(('127.0.0.1',relay.port),timeout=5)as peer:
                    request=('POST /responses HTTP/1.1\r\nHost: 127.0.0.1:'+str(relay.port)+'\r\nAuthorization: Bearer '+relay.token+'\r\nContent-Length: '+str(module.MAX_REQUEST+1)+'\r\nConnection: close\r\n\r\n')
                    peer.sendall(request.encode());response=http.client.HTTPResponse(peer);response.begin()
                    assert response.status==400
                    assert b'owned model relay refused request'in response.read()
            assert not seen
        finally:relay.close()


def test_upstream_redirect_never_forwards_credential_to_redirect_target():
    with upstream()as(trap,trap_seen),upstream(redirect=trap+'/steal')as(base,seen):
        relay=module.Relay(base,'SYNTHETIC_SECRET','unit-model',20)
        try:
            response=httpx.post(relay.url+'/responses',headers={'Authorization':'Bearer '+relay.token},json={'model':'unit-model','stream':True})
            assert response.status_code==307;relay.wait_for_idle();assert len(seen)==1 and trap_seen==[]
            assert relay.snapshot()['failed_responses']==1
        finally:relay.close()

@pytest.mark.parametrize('base',['https://user:pass@example.com','https://example.com?key=value','https://example.com#fragment','http://example.com','file:///tmp','http://localhost:9011','https://example.com:bad','https://example.com/ bad'])
def test_endpoint_refusal(base):
    with pytest.raises(ValueError):module.settings(base,'SYNTHETIC_SECRET','unit-model')
