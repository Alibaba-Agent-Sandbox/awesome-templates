"""Owned browser task fixture; no model or external service."""
import argparse,http.server,json,threading
p=argparse.ArgumentParser();p.add_argument('--port',type=int,required=True);p.add_argument('--nonce',required=True);args=p.parse_args()
lock=threading.Lock();state={'count':0,'code':''};prefix='/'+args.nonce+'/'
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self,*a):pass
    def send(self,code,body,kind='application/json'):
        self.send_response(code);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    def do_GET(self):
        if self.path==prefix+'state':
            with lock:body=json.dumps(state).encode()
            self.send(200,body)
        elif self.path==prefix:
            body=b"""<!doctype html><html><title>Owned browser verification</title><h1>Browser task</h1><p>Count: <span id='count'>0</span></p><button id='inc' onclick="fetch('click',{method:'POST'}).then(r=>r.json()).then(v=>document.getElementById('count').textContent=v.count)">Increment</button><label>Verification code <input id='code' aria-label='Verification code'></label><button id='submit' onclick="fetch('submit',{method:'POST',body:document.getElementById('code').value}).then(r=>r.json()).then(v=>document.getElementById('saved').textContent=v.code)">Submit</button><p>Saved: <span id='saved'></span></p></html>"""
            self.send(200,body,'text/html; charset=utf-8')
        else:self.send(404,b'{}')
    def do_POST(self):
        size=int(self.headers.get('Content-Length','0'))
        if not 0<=size<=4096:self.send(413,b'{}');return
        body=self.rfile.read(size)
        with lock:
            if self.path==prefix+'click':state['count']+=1
            elif self.path==prefix+'submit':state['code']=body.decode()
            else:self.send(404,b'{}');return
            result=json.dumps(state).encode()
        self.send(200,result)
http.server.ThreadingHTTPServer(('0.0.0.0',args.port),H).serve_forever()
