"""Bounded authored Google GenerateContent / OpenAI Chat text/tool transport adapter.
Original Gemini CLI owns planning and tool execution. No hosted account claim.
"""
import contextlib,json,secrets,threading,time,urllib.error,urllib.request
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlsplit

MAX_REQUEST=2*1024*1024
MAX_RESPONSE=4*1024*1024
TOOLS={'read_file','write_file','replace','run_shell_command','list_directory','glob','grep_search'}


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


def text(parts):
    if not isinstance(parts,list)or any(not isinstance(p,dict)or set(p)!={'text'}or not isinstance(p['text'],str)for p in parts):raise ValueError('plain native text required')
    return '\n'.join(p['text']for p in parts)


def schema(value):
    if isinstance(value,list):return [schema(v)for v in value]
    if not isinstance(value,dict):return value
    result={k:schema(v)for k,v in value.items()if k not in ['propertyOrdering','nullable']}
    if isinstance(result.get('type'),str):result['type']=result['type'].lower()
    if value.get('nullable')is True and isinstance(result.get('type'),str):result['type']=[result['type'],'null']
    return result


def request(data,model):
    if not isinstance(data,dict):raise ValueError('native object required')
    messages=[];pending={};turn=0
    if data.get('systemInstruction'):messages.append({'role':'system','content':text(data['systemInstruction'].get('parts',[]))})
    history=data.get('contents')
    if not isinstance(history,list)or not history or len(history)>128:raise ValueError('bounded native history required')
    for m in history:
        role={'user':'user','model':'assistant'}.get(m.get('role'))
        if role is None:raise ValueError('unsupported native role')
        parts=m.get('parts')
        if not isinstance(parts,list):raise ValueError('native parts required')
        texts=[];calls=[];results=[]
        for index,p in enumerate(parts):
            if set(p)=={'text'}:texts.append(text([p]))
            elif role=='assistant' and (set(p)=={'functionCall'} or (
                set(p)=={'functionCall','thoughtSignature'} and
                p['thoughtSignature']=='skip_thought_signature_validator'
            )):
                f=p['functionCall'];name=f.get('name');arguments=f.get('args');identifier=f.get('id')or'call_'+str(turn)+'_'+str(index)
                if name not in TOOLS or not isinstance(arguments,dict)or not isinstance(identifier,str):raise ValueError('unsupported native function')
                calls.append({'id':identifier,'type':'function','function':{'name':name,'arguments':json.dumps(arguments)}});pending.setdefault(name,[]).append(identifier)
            elif set(p)=={'functionResponse'}and role=='user':
                f=p['functionResponse'];name=f.get('name');queue=pending.get(name,[])
                if name not in TOOLS or not queue or not isinstance(f.get('response'),dict):raise ValueError('native function response identity differs')
                identifier=queue.pop(0)
                if f.get('id')and f['id']!=identifier:raise ValueError('native function response id differs')
                results.append({'role':'tool','tool_call_id':identifier,'content':json.dumps(f['response'])})
            else:raise ValueError('unsupported image/thinking/content')
        messages.extend(results)
        if texts or calls:
            item={'role':role,'content':'\n'.join(texts)}
            if calls:item['tool_calls']=calls
            messages.append(item)
        turn+=1
    tools=[]
    for group in data.get('tools',[]):
        if set(group)!={'functionDeclarations'}:raise ValueError('only original text tool declarations supported')
        for t in group['functionDeclarations']:
            if t.get('name')not in TOOLS:raise ValueError('unsupported native tool')
            parameters=t.get('parametersJsonSchema',t.get('parameters',{'type':'object'}))
            if not isinstance(parameters,dict):raise ValueError('native tool schema required')
            tools.append({'type':'function','function':{'name':t['name'],'description':t.get('description',''),'parameters':schema(parameters)}})
    config=data.get('generationConfig',{})
    thinking=config.get('thinkingConfig',{})
    if thinking.get('includeThoughts')or thinking.get('thinkingBudget',0)not in [None,0]:raise ValueError('thinking unsupported')
    value={'model':model,'messages':messages,'stream':False,'max_tokens':min(8192,max(1,int(config.get('maxOutputTokens',4096))))}
    if tools:value.update(tools=tools,tool_choice='auto',parallel_tool_calls=False)
    if data.get('toolConfig',{}).get('functionCallingConfig',{}).get('mode')not in [None,'AUTO']:raise ValueError('only auto native function selection supported')
    if config.get('stopSequences'):value['stop']=config['stopSequences']
    return value


def reply(value,model):
    choices=value.get('choices')
    if not isinstance(choices,list)or len(choices)!=1:raise ValueError('one completed model choice required')
    choice=choices[0];message=choice.get('message',{});finish=choice.get('finish_reason')
    if finish not in ['stop','tool_calls']:raise ValueError('model response incomplete')
    parts=[];content=message.get('content')
    if content:
        if not isinstance(content,str):raise ValueError('text reply required')
        parts.append({'text':content})
    calls=message.get('tool_calls',[])
    if not isinstance(calls,list)or len(calls)>8:raise ValueError('bounded tool requests required')
    for c in calls:
        f=c.get('function',{});args=json.loads(f.get('arguments',''))
        if c.get('type')!='function'or f.get('name')not in TOOLS or not isinstance(args,dict)or not isinstance(c.get('id'),str)or not c['id']:raise ValueError('unsupported original function request')
        parts.append({'functionCall':{'id':c['id'],'name':f['name'],'args':args}})
    if bool(calls)!=(finish=='tool_calls')or not parts:raise ValueError('tool completion differs')
    usage=value.get('usage',{});counts={}
    for source,target in [('prompt_tokens','promptTokenCount'),('completion_tokens','candidatesTokenCount')]:
        n=usage.get(source)
        if type(n)is not int or n<0:raise ValueError('actual token usage required')
        counts[target]=n
    counts['totalTokenCount']=sum(counts.values())
    return {'candidates':[{'index':0,'content':{'role':'model','parts':parts},'finishReason':'STOP'}],'modelVersion':model,'usageMetadata':counts}


def events(message):
    yield '',message


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):return None


class Relay:
    def __init__(self,base,key,model,timeout):
        self.base,self.key,self.model=settings(base,key,model);self.token=secrets.token_urlsafe(32);self.deadline=time.monotonic()+timeout
        self.stats={'model_requests':0,'completed_responses':0,'failed_responses':0,'native_tool_calls':0,'native_tool_results':0}
        self.lock=threading.Lock();self.handlers=set();self.responses=set();self.closed=False;self.failure_counts={};self.last_upstream_status=0
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
                if owner.closed or self.headers.get('Authorization')!='Bearer '+owner.token or self.path!='/v1beta/models/'+owner.model+':streamGenerateContent?alt=sse':self.refuse(403);return
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
                    stage='upstream_open'
                    response=owner.opener.open(req,timeout=max(1,min(60,owner.deadline-time.monotonic())))
                    owner.last_upstream_status=response.status;stage='upstream_read'
                    with owner.lock:owner.responses.add(response)
                    raw=response.read(MAX_RESPONSE+1)
                    if len(raw)>MAX_RESPONSE or owner.closed or time.monotonic()>=owner.deadline:raise ValueError('bounded upstream reply exceeded')
                    stage='reply_shape';message=reply(json.loads(raw),owner.model);stage='native_stream'
                    self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
                    for kind,value in events(message):self.wfile.write(('data: '+json.dumps(value)+'\n\n').encode())
                    self.wfile.flush()
                    with owner.lock:
                        owner.stats['completed_responses']+=1
                        owner.stats['native_tool_calls']+=sum('functionCall'in b for b in message['candidates'][0]['content']['parts'])
                except (OSError,ValueError,TypeError,KeyError,AttributeError)as exc:
                    with owner.lock:
                        owner.stats['failed_responses']+=1
                        label=stage+('_http_'+str(exc.code)if isinstance(exc,urllib.error.HTTPError)else'_'+type(exc).__name__)
                        owner.failure_counts[label]=owner.failure_counts.get(label,0)+1
                        if isinstance(exc,urllib.error.HTTPError):owner.last_upstream_status=exc.code
                    with contextlib.suppress(OSError):self.refuse(502)
                finally:
                    if response is not None:
                        response.close()
                        with owner.lock:owner.responses.discard(response)
        self.server=Server(('127.0.0.1',0),Handler);self.port=self.server.server_address[1];self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
    @property
    def url(self):return 'http://127.0.0.1:'+str(self.port)
    def snapshot(self):
        with self.lock:return {**self.stats,'failure_counts':dict(self.failure_counts),'last_upstream_status':self.last_upstream_status}
    def wait_for_idle(self,timeout=65):
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            with self.lock:busy=bool(self.handlers)
            if not busy:return
            time.sleep(.02)
        raise RuntimeError('owned Gemini adapter RPC drain unconfirmed')
    def close(self):
        if self.closed:return
        self.closed=True;self.server.shutdown();self.server.server_close();self.thread.join(timeout=2)
        with self.lock:responses=list(self.responses);handlers=list(self.handlers)
        for response in responses:
            with contextlib.suppress(OSError):response.close()
        deadline=time.monotonic()+65
        for handler in handlers:handler.join(timeout=max(0,deadline-time.monotonic()))
        if self.thread.is_alive()or any(h.is_alive()for h in handlers):raise RuntimeError('owned Gemini adapter cleanup unconfirmed')
        import socket
        with socket.socket()as probe:
            probe.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);probe.bind(('127.0.0.1',self.port))
