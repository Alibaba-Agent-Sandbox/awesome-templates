"""Bounded authored Anthropic Messages / OpenAI Chat text/tool transport adapter.
Original Claude Code owns planning and tool execution. No hosted account claim.
"""
import contextlib,json,secrets,threading,time,urllib.error,urllib.request
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlsplit

MAX_REQUEST=2*1024*1024
MAX_RESPONSE=4*1024*1024
TOOLS={'Read','Edit','Write','Bash'}


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


def text(blocks):
    if isinstance(blocks,str):return blocks
    if not isinstance(blocks,list):raise ValueError('text blocks required')
    if any(not isinstance(b,dict)or b.get('type')!='text'or not isinstance(b.get('text'),str)for b in blocks):raise ValueError('only text content is supported')
    return '\n'.join(b['text']for b in blocks)


def request(data,model):
    if not isinstance(data,dict)or data.get('model')!=model or data.get('stream')is not True:raise ValueError('explicit streamed selected model required')
    if data.get('thinking',{}).get('type')not in [None,'disabled']:raise ValueError('extended thinking unsupported by this profile')
    messages=[];system=data.get('system')
    if system:messages.append({'role':'system','content':text(system)})
    history=data.get('messages')
    if not isinstance(history,list)or not history or len(history)>128:raise ValueError('bounded message list required')
    for m in history:
        role=m.get('role');content=m.get('content')
        if role not in ['user','assistant']:raise ValueError('unsupported role')
        if isinstance(content,str):messages.append({'role':role,'content':content});continue
        if not isinstance(content,list):raise ValueError('content list required')
        parts=[];calls=[];results=[]
        for b in content:
            kind=b.get('type')
            if kind=='text':parts.append(text([b]))
            elif kind=='tool_use'and role=='assistant':
                if b.get('name')not in TOOLS or not isinstance(b.get('input'),dict)or not isinstance(b.get('id'),str):raise ValueError('unsupported native tool')
                calls.append({'id':b['id'],'type':'function','function':{'name':b['name'],'arguments':json.dumps(b['input'])}})
            elif kind=='tool_result'and role=='user':
                if not isinstance(b.get('tool_use_id'),str):raise ValueError('tool identity required')
                value=text(b.get('content',''))
                results.append({'role':'tool','tool_call_id':b['tool_use_id'],'content':value})
            else:raise ValueError('unsupported native content type')
        if parts or calls:
            item={'role':role,'content':'\n'.join(parts)}
            if calls:item['tool_calls']=calls
            messages.append(item)
        messages.extend(results)
    tools=[]
    for tool in data.get('tools',[]):
        if tool.get('name')not in TOOLS or not isinstance(tool.get('input_schema'),dict):raise ValueError('unsupported native tool schema')
        tools.append({'type':'function','function':{'name':tool['name'],'description':tool.get('description',''),'parameters':tool['input_schema']}})
    value={'model':model,'messages':messages,'stream':False,'max_tokens':min(8192,max(1,int(data.get('max_tokens',4096))))}
    if tools:value.update(tools=tools,tool_choice='auto',parallel_tool_calls=False)
    choice=data.get('tool_choice',{})
    if choice.get('type')not in [None,'auto']:raise ValueError('only automatic native tool selection supported')
    if data.get('stop_sequences'):value['stop']=data['stop_sequences']
    return value


def reply(value,model):
    choices=value.get('choices')
    if not isinstance(choices,list)or len(choices)!=1:raise ValueError('one completed model choice required')
    choice=choices[0];message=choice.get('message',{});finish=choice.get('finish_reason')
    if finish not in ['stop','tool_calls']:raise ValueError('model response incomplete')
    blocks=[];content=message.get('content')
    if content:
        if not isinstance(content,str):raise ValueError('text reply required')
        blocks.append({'type':'text','text':content})
    calls=message.get('tool_calls',[])
    if not isinstance(calls,list)or len(calls)>8:raise ValueError('bounded native tool requests required')
    for call in calls:
        fn=call.get('function',{});arguments=json.loads(fn.get('arguments',''))
        if call.get('type')!='function'or fn.get('name')not in TOOLS or not isinstance(arguments,dict)or not isinstance(call.get('id'),str)or not call['id']:raise ValueError('invalid native tool request')
        blocks.append({'type':'tool_use','id':call['id'],'name':fn['name'],'input':arguments})
    if bool(calls)!=(finish=='tool_calls')or not blocks:raise ValueError('tool completion differs')
    usage=value.get('usage',{});counts={}
    for source,target in [('prompt_tokens','input_tokens'),('completion_tokens','output_tokens')]:
        n=usage.get(source)
        if type(n)is not int or n<0:raise ValueError('actual token usage required')
        counts[target]=n
    return {'id':'msg_'+secrets.token_hex(16),'type':'message','role':'assistant','model':model,'content':blocks,'stop_reason':'tool_use'if calls else'end_turn','stop_sequence':None,'usage':counts}


def events(message):
    yield 'message_start',{'type':'message_start','message':{**message,'content':[],'stop_reason':None,'usage':{**message['usage'],'output_tokens':0}}}
    for i,block in enumerate(message['content']):
        tool=block['type']=='tool_use';initial={**block,'input':{}}if tool else{'type':'text','text':''}
        yield 'content_block_start',{'type':'content_block_start','index':i,'content_block':initial}
        delta={'type':'input_json_delta','partial_json':json.dumps(block['input'])}if tool else{'type':'text_delta','text':block['text']}
        yield 'content_block_delta',{'type':'content_block_delta','index':i,'delta':delta}
        yield 'content_block_stop',{'type':'content_block_stop','index':i}
    yield 'message_delta',{'type':'message_delta','delta':{'stop_reason':message['stop_reason'],'stop_sequence':None},'usage':{'output_tokens':message['usage']['output_tokens']}}
    yield 'message_stop',{'type':'message_stop'}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):return None


class Relay:
    def __init__(self,base,key,model,timeout):
        self.base,self.key,self.model=settings(base,key,model);self.token=secrets.token_urlsafe(32);self.deadline=time.monotonic()+timeout
        self.stats={'model_requests':0,'completed_responses':0,'failed_responses':0,'native_tool_calls':0,'native_tool_results':0}
        self.lock=threading.Lock();self.handlers=set();self.responses=set();self.closed=False
        self.opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect());owner=self
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
                raw=json.dumps({'type':'error','error':{'type':'invalid_request_error','message':'bounded owned transport refused request'}}).encode()
                self.send_response(code);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
            def do_GET(self):self.refuse(403)
            def do_POST(self):
                if owner.closed or self.headers.get('Authorization')!='Bearer '+owner.token or self.path not in ['/v1/messages','/v1/messages?beta=true']:self.refuse(403);return
                response=None
                try:
                    size=int(self.headers.get('Content-Length','0'))
                    if not 0<size<=MAX_REQUEST or self.headers.get('Transfer-Encoding'):raise ValueError('bounded request required')
                    data=json.loads(self.rfile.read(size));payload=request(data,owner.model)
                except (ValueError,TypeError,KeyError,AttributeError):self.refuse(400);return
                try:
                    with owner.lock:
                        if owner.closed or owner.stats['model_requests']>=32 or time.monotonic()>=owner.deadline:self.refuse(429);return
                        owner.stats['model_requests']+=1
                        owner.stats['native_tool_results']+=sum(m['role']=='tool'for m in payload['messages'])
                    req=urllib.request.Request(owner.base+'/chat/completions',data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+owner.key,'Content-Type':'application/json'},method='POST')
                    response=owner.opener.open(req,timeout=max(1,min(60,owner.deadline-time.monotonic())))
                    with owner.lock:owner.responses.add(response)
                    raw=response.read(MAX_RESPONSE+1)
                    if len(raw)>MAX_RESPONSE or owner.closed or time.monotonic()>=owner.deadline:raise ValueError('bounded upstream reply exceeded')
                    message=reply(json.loads(raw),owner.model)
                    self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
                    for kind,value in events(message):self.wfile.write(('event: '+kind+'\ndata: '+json.dumps(value)+'\n\n').encode())
                    self.wfile.flush()
                    with owner.lock:
                        owner.stats['completed_responses']+=1
                        owner.stats['native_tool_calls']+=sum(b['type']=='tool_use'for b in message['content'])
                except (OSError,ValueError,TypeError,KeyError,AttributeError):
                    with owner.lock:owner.stats['failed_responses']+=1
                    with contextlib.suppress(OSError):self.refuse(502)
                finally:
                    if response is not None:
                        response.close()
                        with owner.lock:owner.responses.discard(response)
        self.server=Server(('127.0.0.1',0),Handler);self.port=self.server.server_address[1];self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
    @property
    def url(self):return 'http://127.0.0.1:'+str(self.port)
    def snapshot(self):
        with self.lock:return dict(self.stats)
    def wait_for_idle(self,timeout=65):
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            with self.lock:busy=bool(self.handlers)
            if not busy:return
            time.sleep(.02)
        raise RuntimeError('owned Claude adapter RPC drain unconfirmed')
    def close(self):
        if self.closed:return
        self.closed=True;self.server.shutdown();self.server.server_close();self.thread.join(timeout=2)
        with self.lock:responses=list(self.responses);handlers=list(self.handlers)
        for response in responses:
            with contextlib.suppress(OSError):response.close()
        deadline=time.monotonic()+65
        for handler in handlers:handler.join(timeout=max(0,deadline-time.monotonic()))
        if self.thread.is_alive()or any(h.is_alive()for h in handlers):raise RuntimeError('owned Claude adapter cleanup unconfirmed')
        import socket
        with socket.socket()as probe:
            probe.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);probe.bind(('127.0.0.1',self.port))
