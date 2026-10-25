"""Actual authored RFB wire fixture and native relay authentication boundaries."""
import asyncio,importlib.util,io,struct,sys
from pathlib import Path
import pytest


def load(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file))
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

r=load('chrome_rfb_protocol_tests','rfb.py')


def test_actual_authored_rfb_roundtrip_and_pointer_reaches_server():
    async def run():
        from Crypto.Cipher import DES
        from PIL import Image
        received=[];password='pass1234';challenge=bytes(range(16))
        async def handler(reader,writer):
            try:
                writer.write(b'RFB 003.008\n');await writer.drain();assert await reader.readexactly(12)==b'RFB 003.008\n'
                writer.write(b'\x01\x02');await writer.drain();assert await reader.readexactly(1)==b'\x02'
                writer.write(challenge);await writer.drain();answer=await reader.readexactly(16)
                key=bytes(int(f'{x:08b}'[::-1],2)for x in password.encode());assert answer==DES.new(key,DES.MODE_ECB).encrypt(challenge)
                writer.write(b'\x00'*4);await writer.drain();assert await reader.readexactly(1)==b'\x01'
                writer.write(struct.pack('>HH',4,3)+struct.pack('>BBBBHHHBBBxxx',32,24,0,1,255,255,255,16,8,0)+struct.pack('>I',7)+b'fixture');await writer.drain()
                received.append(await reader.readexactly(6));received.append(await reader.readexactly(6))
                assert await reader.readexactly(20)==b'\x00'*4+struct.pack('>BBBBHHHBBBxxx',32,24,0,1,255,255,255,16,8,0)
                assert await reader.readexactly(8)==struct.pack('>BBHi',2,0,1,0)
                assert await reader.readexactly(10)==struct.pack('>BBHHHH',3,0,0,0,4,3)
                writer.write(b'\x00\x00\x00\x01'+struct.pack('>HHHHi',0,0,4,3,0)+bytes([56,34,12,0])*12);await writer.drain()
            finally:writer.close();await writer.wait_closed()
        server=await asyncio.start_server(handler,'127.0.0.1',0)
        try:
            raw,width,height=await r.capture_tcp(server.sockets[0].getsockname()[1],password,pointer=(2,1))
            image=Image.open(io.BytesIO(raw));image.load()
            assert (width,height)==(4,3)and image.getpixel((0,0))==(12,34,56)
            assert received==[struct.pack('>BBHH',5,1,2,1),struct.pack('>BBHH',5,0,2,1)]
        finally:server.close();await server.wait_closed()
    asyncio.run(run())


@pytest.mark.parametrize('header',[b'RFB 003.003\n',b'not a header'])
def test_wrong_native_protocol_fails_before_authentication(header):
    async def run():
        async def read(count):return header
        async def write(data):pytest.fail('wrong protocol must never send credentials')
        with pytest.raises(RuntimeError,match='RFB3.8'):await r.capture(read,write,'pass1234')
    asyncio.run(run())


def test_actual_http_relay_rejects_missing_or_wrong_bearer_before_native():
    relay=load('chrome_cdp_auth_boundary_tests','relay.py')
    async def run():
        import aiohttp
        from aiohttp import web
        relay.TOKEN='synthetic-server-token';app=web.Application();app.router.add_get('/json/version',relay.cdp_http)
        runner=web.AppRunner(app);await runner.setup();site=web.TCPSite(runner,'127.0.0.1',0);await site.start()
        try:
            port=site._server.sockets[0].getsockname()[1]
            async with aiohttp.ClientSession()as client:
                for headers in [{},{'Authorization':'Bearer wrong'}]:
                    async with client.get(f'http://127.0.0.1:{port}/json/version',headers=headers)as response:assert response.status==401
        finally:await runner.cleanup()
    asyncio.run(run())


def test_real_cdp_client_activates_selected_page_before_observing_visibility():
    cdp=load('chrome_page_activation_tests','cdp.py')
    async def run():
        import aiohttp
        from aiohttp import web
        calls=[]
        async def listing(request):return web.json_response([{'type':'page','id':'owned','webSocketDebuggerUrl':'ws://native.invalid/devtools/page/owned'}])
        async def websocket(request):
            ws=web.WebSocketResponse();await ws.prepare(request)
            async for message in ws:
                assert message.type==aiohttp.WSMsgType.TEXT
                value=message.json();calls.append(value['method'])
                await ws.send_json({'id':value['id'],'result':{}})
            return ws
        app=web.Application();app.router.add_get('/json/list',listing);app.router.add_get('/devtools/page/owned',websocket)
        runner=web.AppRunner(app);await runner.setup();site=web.TCPSite(runner,'127.0.0.1',0);await site.start()
        try:
            async with cdp.Page('http://127.0.0.1:'+str(site._server.sockets[0].getsockname()[1])):pass
            assert calls==['Page.bringToFront','Page.enable']
        finally:await runner.cleanup()
    asyncio.run(run())


def test_visible_native_fixture_validation_ignores_center_pointer_but_requires_all_content_regions(monkeypatch):
    from PIL import Image
    monkeypatch.syspath_prepend(str(Path(__file__).parent))
    worker=load('chrome_native_fixture_color_tests','worker.py')
    screenshot=Image.new('RGB',(1024,768),(10,230,20))
    screenshot.putpixel((512,384),(255,255,255))
    assert worker.fixture_frame_matches(screenshot,(10,230,20)) is True
    screenshot.putpixel((768,576),(255,255,255))
    assert worker.fixture_frame_matches(screenshot,(10,230,20)) is False
    assert worker.fixture_frame_matches(Image.new('RGB',(1024,768),'white'),(10,230,20)) is False


@pytest.mark.parametrize('prefix,query',[('', ''),('/provider/ports/9222','route=owned'),('/provider/ports/9222/','route=owned')])
def test_cdp_retains_provider_path_query_and_both_authentication_headers(prefix,query):
    cdp=load('chrome_prefixed_cdp_tests','cdp.py')
    async def run():
        import aiohttp
        from aiohttp import web
        calls=[]
        headers={'Authorization':'Bearer synthetic-app','X-Provider-Token':'synthetic-gateway'}
        async def authenticate(request,handler):
            assert request.query_string==query
            assert all(request.headers.get(key)==value for key,value in headers.items())
            return await handler(request)
        middleware=web.middleware(authenticate)
        async def listing(request):
            calls.append('list')
            return web.json_response([{'type':'page','id':'owned','webSocketDebuggerUrl':'ws://unreachable.invalid/devtools/page/owned'}])
        async def websocket(request):
            calls.append('websocket');ws=web.WebSocketResponse();await ws.prepare(request)
            async for message in ws:
                value=message.json();calls.append(value['method'])
                await ws.send_json({'id':value['id'],'result':{}})
            return ws
        app=web.Application(middlewares=[middleware]);route=prefix.rstrip('/')
        app.router.add_get(route+'/json/list',listing);app.router.add_get(route+'/devtools/page/owned',websocket)
        runner=web.AppRunner(app);await runner.setup();site=web.TCPSite(runner,'127.0.0.1',0);await site.start()
        try:
            base='http://127.0.0.1:'+str(site._server.sockets[0].getsockname()[1])+prefix+('?' + query if query else '')
            async with cdp.Page(base,headers=headers):pass
            assert calls==['list','websocket','Page.bringToFront','Page.enable']
        finally:await runner.cleanup()
    asyncio.run(run())


def test_vnc_websocket_retains_distinct_provider_path_and_fixed_query():
    cdp=load('chrome_prefixed_vnc_tests','cdp.py')
    async def run():
        import aiohttp
        from aiohttp import web
        async def websocket(request):
            assert request.query_string=='route=vnc'
            assert request.headers.get('Authorization')=='Bearer synthetic-app'
            assert request.headers.get('X-Provider-Token')=='synthetic-gateway'
            ws=web.WebSocketResponse();await ws.prepare(request);await ws.send_str('owned-vnc-route');await ws.close();return ws
        app=web.Application();app.router.add_get('/provider/ports/6080/websockify',websocket)
        runner=web.AppRunner(app);await runner.setup();site=web.TCPSite(runner,'127.0.0.1',0);await site.start()
        try:
            base='http://127.0.0.1:'+str(site._server.sockets[0].getsockname()[1])+'/provider/ports/6080?route=vnc'
            async with aiohttp.ClientSession()as session:
                async with session.ws_connect(cdp.endpoint_url(base,'/websockify',websocket=True),headers={'Authorization':'Bearer synthetic-app','X-Provider-Token':'synthetic-gateway'})as ws:
                    assert (await ws.receive()).data=='owned-vnc-route'
            assert cdp.endpoint_url('https://provider.invalid/prefix?fixed=1','ws://native.invalid/devtools/page/owned?native=2',websocket=True)=='wss://provider.invalid/prefix/devtools/page/owned?fixed=1&native=2'
        finally:await runner.cleanup()
    asyncio.run(run())
