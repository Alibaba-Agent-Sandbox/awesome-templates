"""Bounded local catalogue/credential relay; original Responses bytes pass unchanged."""
import contextlib,json,secrets,threading,time,urllib.error,urllib.request
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlsplit

MAX_REQUEST=2*1024*1024
MAX_RESPONSE=4*1024*1024


def settings(base,key,model):
    import re
    if not all(isinstance(v,str)and v for v in [base,key,model]):raise ValueError('explicit model base/key/model required')
    if len(base)>2048 or any(c.isspace()or ord(c)<32 for c in base):raise ValueError('invalid bounded model base')
    parsed=urlsplit(base)
    try:parsed.port
    except ValueError:raise ValueError('invalid model base port')from None
    if not parsed.hostname or parsed.username is not None or parsed.password is not None or parsed.query or parsed.fragment or(parsed.scheme!='https'and not(parsed.scheme=='http'and parsed.hostname in ['127.0.0.1','::1'])):raise ValueError('explicit HTTPS or literal-loopback HTTP model base required')
    if len(key)>8192 or any(ord(c)<32 for c in key):raise ValueError('invalid bounded model key')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}',model):raise ValueError('invalid model identifier')
    return base.rstrip('/'),key,model


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):return None


class Relay:
    def __init__(self,base,key,model,timeout):
        self.base,self.key,self.model=settings(base,key,model)
        self.token=secrets.token_urlsafe(32);self.deadline=time.monotonic()+timeout
        self.stats={'catalog_requests':0,'responses_requests':0,'completed_responses':0,'failed_responses':0}
        self.lock=threading.Lock();self.handlers=set();self.responses=set();self.closed=False
        self.opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
        owner=self
        class Server(ThreadingHTTPServer):
            daemon_threads=True
            def handle_error(self,request,client_address):
                with owner.lock:owner.stats['failed_responses']+=1
        class Handler(BaseHTTPRequestHandler):
            def setup(self):
                super().setup();self.connection.settimeout(5)
                with owner.lock:owner.handlers.add(threading.current_thread())
            def finish(self):
                try:super().finish()
                finally:
                    with owner.lock:owner.handlers.discard(threading.current_thread())
            def log_message(self,*args):pass
            def refuse(self,code):
                data=json.dumps({'error':{'message':'owned model relay refused request','type':'invalid_request_error'}}).encode()
                self.send_response(code);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
            def authorized(self):return not owner.closed and self.headers.get('Authorization')=='Bearer '+owner.token
            def do_GET(self):
                if not self.authorized()or self.path!='/muse-code/models':self.refuse(403);return
                with owner.lock:owner.stats['catalog_requests']+=1
                data=json.dumps({'object':'list','data':[{'id':owner.model,'object':'model','created':1,'owned_by':'explicit-approved-compatible-model'}]}).encode()
                self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
            def do_POST(self):
                if not self.authorized()or self.path!='/responses':self.refuse(403);return
                try:
                    length=int(self.headers.get('Content-Length','0'))
                    if not 0<length<=MAX_REQUEST or self.headers.get('Transfer-Encoding'):raise ValueError()
                    raw=self.rfile.read(length);data=json.loads(raw)
                    if not isinstance(data,dict)or data.get('model')!=owner.model or data.get('stream')is not True:raise ValueError()
                except (ValueError,TypeError):self.refuse(400);return
                response=None
                try:
                    with owner.lock:
                        if owner.closed or owner.stats['responses_requests']>=32 or time.monotonic()>=owner.deadline:self.refuse(429);return
                        owner.stats['responses_requests']+=1
                    request=urllib.request.Request(owner.base+'/responses',data=raw,headers={'Authorization':'Bearer '+owner.key,'Content-Type':'application/json'},method='POST')
                    try:response=owner.opener.open(request,timeout=max(1,min(30,owner.deadline-time.monotonic())))
                    except urllib.error.HTTPError as exc:response=exc
                    with owner.lock:owner.responses.add(response)
                    self.send_response(response.status);self.send_header('Content-Type',response.headers.get('Content-Type','application/json'));self.end_headers()
                    total=0
                    while chunk:=response.read1(65536):
                        total+=len(chunk)
                        if total>MAX_RESPONSE or owner.closed or time.monotonic()>=owner.deadline:raise ValueError('bounded original Responses relay exceeded')
                        self.wfile.write(chunk);self.wfile.flush()
                    with owner.lock:owner.stats['completed_responses'if response.status==200 else'failed_responses']+=1
                except (OSError,ValueError):
                    with owner.lock:owner.stats['failed_responses']+=1
                finally:
                    if response is not None:
                        response.close()
                        with owner.lock:owner.responses.discard(response)
        self.server=Server(('127.0.0.1',0),Handler);self.port=self.server.server_address[1]
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()

    @property
    def url(self):return 'http://127.0.0.1:'+str(self.port)

    def snapshot(self):
        with self.lock:return dict(self.stats)

    def wait_for_idle(self,timeout=35):
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            with self.lock:busy=bool(self.handlers)
            if not busy:return
            time.sleep(.02)
        raise RuntimeError('owned Muse issued Responses cleanup not confirmed')

    def close(self):
        if self.closed:return
        self.closed=True;self.server.shutdown();self.server.server_close();self.thread.join(timeout=2)
        with self.lock:responses=list(self.responses);handlers=list(self.handlers)
        deadline=time.monotonic()+35
        for response in responses:
            with contextlib.suppress(OSError):response.close()
        for handler in handlers:handler.join(timeout=max(0,deadline-time.monotonic()))
        if self.thread.is_alive()or any(h.is_alive()for h in handlers):raise RuntimeError('owned Muse relay cleanup not confirmed')
        # Server close must release its exact owned listener, not a random route.
        import socket
        with socket.socket()as probe:
            probe.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);probe.bind(('127.0.0.1',self.port))
