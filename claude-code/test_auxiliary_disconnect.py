"""Real socket disconnects with fixed authored HTTP data, no native/model execution."""
import hashlib,importlib.util,json,socket,struct,threading,http.client,select
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import pytest
spec=importlib.util.spec_from_file_location('claude_disconnect_fixture',Path(__file__).with_name('relay.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)

@pytest.mark.parametrize('kind',['optional','required','unknown'])
def test_peer_disconnect_is_separate_only_for_pinned_optional_request(monkeypatch,kind):
    prompt='Fixed authored optional analysis fixture.'
    monkeypatch.setattr(r,'OPTIONAL_SYSTEM_PREFIX',prompt,raising=False)
    monkeypatch.setattr(r,'OPTIONAL_SYSTEM_BYTES',len(prompt.encode()),raising=False)
    monkeypatch.setattr(r,'OPTIONAL_SYSTEM_SHA256',hashlib.sha256(prompt.encode()).hexdigest(),raising=False)
    entered=threading.Event();release=threading.Event()
    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            self.rfile.read(int(self.headers['Content-Length']));entered.set();assert release.wait(5)
            raw=json.dumps({'choices':[{'message':{'role':'assistant','content':'FIXED'},'finish_reason':'stop'}],'usage':{'prompt_tokens':1,'completion_tokens':1}}).encode()
            self.send_response(200);self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
        def log_message(self,*args):pass
    upstream=ThreadingHTTPServer(('127.0.0.1',0),H);thread=threading.Thread(target=upstream.serve_forever,daemon=True);thread.start()
    relay=r.Relay('http://127.0.0.1:'+str(upstream.server_port)+'/v1','fixed-key','owned-model',10)
    accepted={}
    original_accept=relay.server.get_request
    def accept():
        pair=original_accept();accepted['socket']=pair[0];return pair
    relay.server.get_request=accept
    client=http.client.HTTPConnection('127.0.0.1',relay.port,timeout=3)
    try:
        data={'model':'owned-model','stream':True,'system':[{'type':'text','text':prompt if kind!='unknown'else'Unknown analysis'}],'messages':[{'role':'user','content':'Command: fixed\nOutput: fixed'}],'tools':[]}
        if kind=='required':data['tools']=[{'name':'Read','input_schema':{'type':'object'}}]
        client.request('POST','/v1/messages',body=json.dumps(data).encode(),headers={'Authorization':'Bearer '+relay.token,'Content-Type':'application/json'})
        assert entered.wait(5),relay.snapshot()
        client.sock.setsockopt(socket.SOL_SOCKET,socket.SO_LINGER,struct.pack('ii',1,0));client.close()
        peer=accepted['socket'];assert select.select([peer],[],[],3)[0]
        try:assert peer.recv(1,socket.MSG_PEEK)==b''
        except ConnectionResetError:pass
        release.set();relay.wait_for_idle()
        stats=relay.snapshot();assert stats['completed_responses']==0
        assert stats['failed_responses']==(0 if kind=='optional'else 1)
        assert stats.get('cancelled_auxiliary_responses',0)==(1 if kind=='optional'else 0)
    finally:
        client.close();release.set();relay.close();upstream.shutdown();upstream.server_close();thread.join(3)
