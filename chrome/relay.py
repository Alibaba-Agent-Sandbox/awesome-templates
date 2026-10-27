"""Transparent bounded native CDP and noVNC WebSocket/TCP relays."""
import asyncio,contextlib,hmac,json,os
from urllib.parse import urlsplit
import aiohttp
from aiohttp import web

LIMIT=4*1024*1024
TOKEN=os.environ.get('ABX_SERVER_TOKEN','')


def authorized(request):
    if TOKEN:
        authorization=request.headers.get('Authorization')
        supplied=authorization if authorization is not None else 'Bearer '+request.headers.get('X-Access-Token','')
        if not hmac.compare_digest(supplied,'Bearer '+TOKEN):raise web.HTTPUnauthorized()


async def cdp_http(request):
    authorized(request)
    if request.method not in ['GET','PUT','DELETE']:raise web.HTTPMethodNotAllowed(request.method,['GET','PUT','DELETE'])
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30),trust_env=False)as session:
        async with session.request(request.method,'http://127.0.0.1:9223'+request.raw_path)as response:
            raw=await response.content.read(LIMIT+1)
            if len(raw)>LIMIT:raise web.HTTPBadGateway()
            try:value=json.loads(raw)
            except ValueError:return web.Response(body=raw,status=response.status,content_type='text/plain')
            def rewrite(item):
                if isinstance(item,list):return[rewrite(x)for x in item]
                if isinstance(item,dict):
                    value={k:rewrite(v)for k,v in item.items()}
                    if isinstance(value.get('webSocketDebuggerUrl'),str):
                        path=urlsplit(value['webSocketDebuggerUrl']).path
                        scheme='wss'if request.headers.get('X-Forwarded-Proto',request.scheme)=='https'else'ws'
                        value['webSocketDebuggerUrl']=scheme+'://'+request.host+path
                    return value
                return item
            return web.json_response(rewrite(value),status=response.status)


async def cdp_ws(request):
    authorized(request)
    incoming=web.WebSocketResponse(max_msg_size=LIMIT,heartbeat=20);await incoming.prepare(request)
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=None),trust_env=False)as session:
        async with session.ws_connect('http://127.0.0.1:9223'+request.raw_path,max_msg_size=LIMIT,heartbeat=20)as outgoing:
            async def copy(source,target):
                async for message in source:
                    if message.type==aiohttp.WSMsgType.TEXT:await target.send_str(message.data)
                    elif message.type==aiohttp.WSMsgType.BINARY:await target.send_bytes(message.data)
                    elif message.type==aiohttp.WSMsgType.ERROR:break
            tasks=[asyncio.create_task(copy(incoming,outgoing)),asyncio.create_task(copy(outgoing,incoming))]
            try:await asyncio.wait(tasks,return_when=asyncio.FIRST_COMPLETED)
            finally:
                for task in tasks:task.cancel()
                await asyncio.gather(*tasks,return_exceptions=True)
                await incoming.close()
    return incoming


async def vnc_ws(request):
    # Authentication is the original VNC challenge; its generated password is
    # never in a URL, argv, static file or public verification record.
    ws=web.WebSocketResponse(protocols=['binary'],max_msg_size=LIMIT,heartbeat=20)
    await ws.prepare(request)
    reader,writer=await asyncio.wait_for(asyncio.open_connection('127.0.0.1',5901),10)
    async def to_socket():
        async for message in ws:
            if message.type!=aiohttp.WSMsgType.BINARY:raise RuntimeError('VNC requires binary frames')
            writer.write(message.data);await writer.drain()
    async def to_websocket():
        while value:=await reader.read(65536):await ws.send_bytes(value)
    tasks=[asyncio.create_task(to_socket()),asyncio.create_task(to_websocket())]
    try:await asyncio.wait(tasks,return_when=asyncio.FIRST_COMPLETED)
    finally:
        for task in tasks:task.cancel()
        await asyncio.gather(*tasks,return_exceptions=True)
        writer.close();await writer.wait_closed();await ws.close()
    return ws


async def main():
    cdp=web.Application(client_max_size=LIMIT)
    cdp.router.add_route('*','/json',cdp_http)
    cdp.router.add_route('*','/json/{tail:.*}',cdp_http)
    cdp.router.add_get('/devtools/{tail:.*}',cdp_ws)
    vnc=web.Application(client_max_size=LIMIT)
    vnc.router.add_get('/websockify',vnc_ws)
    vnc.router.add_static('/','/usr/share/novnc',follow_symlinks=True)
    runners=[]
    try:
        for app,port in [(cdp,9222),(vnc,6080)]:
            runner=web.AppRunner(app,access_log=None);await runner.setup();runners.append(runner)
            await web.TCPSite(runner,'0.0.0.0',port).start()
        await asyncio.Event().wait()
    finally:
        for runner in reversed(runners):await runner.cleanup()


if __name__=='__main__':asyncio.run(main())
