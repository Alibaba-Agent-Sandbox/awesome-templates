"""Actual HTTP/WS and in-memory TLS fixtures; not Express/browser receipts."""
import asyncio
from contextlib import asynccontextmanager
import gzip
import importlib.util
from pathlib import Path
import socket
import ssl
import subprocess

import aiohttp
from aiohttp import web
from aiohttp.test_utils import make_mocked_request
import pytest

spec = importlib.util.spec_from_file_location('ide_preview_relay', Path(__file__).with_name('preview_proxy.py'))
relay_module = importlib.util.module_from_spec(spec); spec.loader.exec_module(relay_module)
PreviewRelay = relay_module.PreviewRelay


@asynccontextmanager
async def backend(ssl_context=None):
    seen = []
    html = b'<html><title>owned preview</title><p>real body</p></html>'
    async def handle(request):
        seen.append(request.path)
        if request.path == '/socket':
            assert request.cookies.get('backend_session') == 'synthetic-session'
            ws = web.WebSocketResponse(protocols=('vscode-test',)); await ws.prepare(request)
            async for message in ws:
                if message.type == aiohttp.WSMsgType.TEXT: await ws.send_str(message.data.upper())
                elif message.type == aiohttp.WSMsgType.BINARY: await ws.send_bytes(message.data[::-1])
            return ws
        if request.path == '/login':
            response = web.Response(body=html, content_type='text/html', headers={'Content-Disposition':'attachment; filename=page.html'})
            response.set_cookie('backend_session','synthetic-session',httponly=True)
            return response
        if request.path == '/download':
            return web.Response(body=b'%PDF-synthetic',content_type='application/pdf',headers={'Content-Disposition':'attachment; filename=file.pdf'})
        if request.path == '/gzip':
            return web.Response(body=gzip.compress(html),content_type='text/html',headers={'Content-Encoding':'gzip','Content-Disposition':'attachment'})
        if request.path == '/redirect':
            return web.Response(status=302,headers={'Location':'https://outside.invalid/?token=synthetic-secret'})
        return web.json_response({'query':dict(request.query),'cookies':dict(request.cookies),'origin':request.headers.get('Origin')})
    app=web.Application();app.router.add_route('*','/{path:.*}',handle)
    runner=web.AppRunner(app,access_log=None);await runner.setup()
    site=web.TCPSite(runner,'127.0.0.1',0,ssl_context=ssl_context);await site.start()
    port=runner.addresses[0][1]
    try:yield ('https' if ssl_context else 'http')+'://127.0.0.1:'+str(port),seen,html
    finally:await runner.cleanup()


def test_transport_rejects_insecure_upstream_and_disabled_tls():
    with pytest.raises(ValueError): PreviewRelay('http://example.invalid')
    with pytest.raises(ValueError): PreviewRelay('https://name:password@example.invalid')
    insecure=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT);insecure.check_hostname=False;insecure.verify_mode=ssl.CERT_NONE
    with pytest.raises(ValueError): PreviewRelay('https://example.invalid',_ssl_context=insecure)


def test_actual_http_html_downloads_auth_query_cookie_isolation_and_origin():
    async def run():
        async with backend() as (url,seen,html):
            async with PreviewRelay(url+'/?token=synthetic-secret',_test_http=True) as relay:
                async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar(unsafe=True)) as client:
                    response=await client.get(relay.origin+'/echo');assert response.status==403
                    # The operator environment routes real invalid Host headers
                    # before the local listener; exercise this guard directly.
                    bad_host=make_mocked_request('GET',relay.entry+'/login',headers={'Host':'outside.invalid'})
                    with pytest.raises(web.HTTPForbidden):await relay._handle(bad_host)
                    response=await client.get(relay.url+'/login',headers={'Origin':'https://outside.invalid'});assert response.status==403
                    assert not seen
                    response=await client.get(relay.url+'/login');assert response.status==200 and await response.read()==html
                    assert 'Content-Disposition' not in response.headers and relay.html_attachment_normalized
                    assert 'backend_session' not in response.headers.get('Set-Cookie','')
                    response=await client.get(relay.origin+'/echo?token=attacker&task=ok',headers={'Origin':relay.origin,'Cookie':relay.cookie+'='+relay.token+'; unrelated_local_cookie=must-not-leak'})
                    body=await response.json();assert body['query']=={'token':'synthetic-secret','task':'ok'}
                    assert body['cookies']=={'backend_session':'synthetic-session'} and body['origin']==url
                    response=await client.get(relay.origin+'/download');assert response.headers['Content-Disposition'].startswith('attachment') and await response.read()==b'%PDF-synthetic'
                    response=await client.get(relay.origin+'/redirect',allow_redirects=False);assert response.status==502
                    assert 'outside.invalid' not in await response.text()
    asyncio.run(run())


def test_actual_websocket_text_binary_subprotocol_auth_and_listener_cleanup():
    async def run():
        async with backend() as (url,seen,html):
            async with PreviewRelay(url,_test_http=True) as relay:
                port=relay.port
                async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar(unsafe=True)) as client:
                    response=await client.get(relay.url+'/login');await response.read()
                    async with client.ws_connect(relay.origin.replace('http:','ws:')+'/socket',origin=relay.origin,protocols=('vscode-test',)) as ws:
                        assert ws.protocol=='vscode-test'
                        await ws.send_str('hello');assert (await ws.receive()).data=='HELLO'
                        await ws.send_bytes(b'\x01\x02');assert (await ws.receive()).data==b'\x02\x01'
            # This environment intercepts connect() even for absent local ports;
            # independently check actual kernel listener release by rebinding.
            with socket.socket() as probe:
                probe.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);probe.bind(('127.0.0.1',port))
            async with aiohttp.ClientSession() as client:
                response=await client.get(url+'/echo');assert response.status==200
    asyncio.run(run())


def test_compressed_html_bytes_remain_encoded_once():
    async def run():
        async with backend() as (url,seen,html):
            async with PreviewRelay(url,_test_http=True) as relay:
                async with aiohttp.ClientSession(auto_decompress=False,cookie_jar=aiohttp.CookieJar(unsafe=True)) as client:
                    response=await client.get(relay.url+'/gzip');data=await response.read()
                    assert response.status==200 and response.headers['Content-Encoding']=='gzip'
                    assert 'Content-Disposition' not in response.headers and gzip.decompress(data)==html
    asyncio.run(run())


def test_failed_socket_close_still_releases_listener_and_http_client():
    async def run():
        async with backend() as (url,seen,html):
            relay=PreviewRelay(url,_test_http=True)
            class FailingSocket:
                async def close(self):raise RuntimeError('synthetic socket close failure')
            with pytest.raises(RuntimeError,match='cleanup not confirmed'):
                async with relay:
                    port=relay.port;relay.sockets.add(FailingSocket())
            assert relay.session.closed
            with socket.socket() as probe:
                probe.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);probe.bind(('127.0.0.1',port))
    asyncio.run(run())


def test_tls_handshake_rejects_unknown_ca_and_accepts_explicit_trust(tmp_path):
    cert=tmp_path/'fixture-cert.pem';key=tmp_path/'fixture-key.pem'
    subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-days','1',
        '-subj','/CN=127.0.0.1','-addext','subjectAltName=IP:127.0.0.1','-addext','basicConstraints=critical,CA:TRUE',
        '-keyout',str(key),'-out',str(cert)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    key.chmod(0o600)
    server=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);server.load_cert_chain(cert,key)
    trusted=ssl.create_default_context(cafile=str(cert))
    def handshake(context):
        incoming,outgoing=ssl.MemoryBIO(),ssl.MemoryBIO();server_in,server_out=ssl.MemoryBIO(),ssl.MemoryBIO()
        client=context.wrap_bio(incoming,outgoing,server_hostname='127.0.0.1')
        peer=server.wrap_bio(server_in,server_out,server_side=True);completed=set()
        for _ in range(100):
            for label,connection in [('client',client),('server',peer)]:
                try:connection.do_handshake();completed.add(label)
                except ssl.SSLWantReadError:pass
            if outgoing.pending:server_in.write(outgoing.read())
            if server_out.pending:incoming.write(server_out.read())
            if len(completed)==2:return
        raise AssertionError('TLS handshake did not complete')
    untrusted=PreviewRelay('https://127.0.0.1')
    with pytest.raises(ssl.SSLCertVerificationError):handshake(untrusted.ssl_context)
    relay=PreviewRelay('https://127.0.0.1',_ssl_context=trusted)
    assert relay.ssl_context.check_hostname and relay.ssl_context.verify_mode==ssl.CERT_REQUIRED
    handshake(relay.ssl_context)


def test_private_entry_redirects_to_canonical_app_path_before_login():
    async def run():
        async with backend() as (url,seen,html):
            async with PreviewRelay(url,_test_http=True) as relay:
                async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar(unsafe=True)) as client:
                    response=await client.get(relay.url+'/login?folder=owned',allow_redirects=False)
                    assert response.status==303
                    assert response.headers['Location']=='/login?folder=owned'
                    assert not seen, 'entry must only exchange the local capability'
                    response=await client.get(relay.origin+response.headers['Location'])
                    assert response.status==200 and await response.read()==html
                    assert seen==['/login']
    asyncio.run(run())


def test_sdk_preview_uses_resolved_provider_headers_and_loopback_http_for_http_and_ws():
    from types import SimpleNamespace
    async def run():
        seen=[]
        async def handler(request):
            assert request.headers.get('X-Provider-Key')=='synthetic-provider-key'
            seen.append((request.path,dict(request.query)))
            if request.headers.get('Upgrade','').lower()=='websocket':
                ws=web.WebSocketResponse();await ws.prepare(request)
                async for message in ws:
                    await ws.send_str(message.data)
                return ws
            return web.Response(text='owned preview')
        app=web.Application();app.router.add_route('*','/{path:.*}',handler);runner=web.AppRunner(app,access_log=None);await runner.setup();site=web.TCPSite(runner,'127.0.0.1',0);await site.start();port=runner.addresses[0][1]
        class Network:
            def get_url(self,port):raise AssertionError('synchronous URL drops required gateway headers')
            async def resolve(self,selected):
                assert selected==3000
                return 'http://127.0.0.1:'+str(port)+'/provider/proxy?fixed=owned',{'X-Provider-Key':'synthetic-provider-key'}
        try:
            async with relay_module.sdk_preview(SimpleNamespace(network=Network()),remote_port=3000)as relay:
                async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar(unsafe=True))as client:
                    response=await client.get(relay.url,headers={'X-Provider-Key':'browser-spoof'});assert response.status==200 and await response.text()=='owned preview'
                    assert 'synthetic-provider-key'not in str(response.headers)
                    async with client.ws_connect(relay.origin+'/ws?fixed=spoof',headers={'X-Provider-Key':'browser-spoof'})as ws:
                        await ws.send_str('native socket');assert(await ws.receive()).data=='native socket'
            assert seen==[('/provider/proxy/',{'fixed':'owned'}),('/provider/proxy/ws',{'fixed':'owned'})]
        finally:await runner.cleanup()
    asyncio.run(run())


@pytest.mark.parametrize('headers',[{'Host':'spoof.invalid'},{'Cookie':'spoof=1'},{'X-Key':'bad\r\nInjected: yes'},{'':'value'}])
def test_resolved_gateway_headers_cannot_inject_hop_host_or_browser_cookie(headers):
    with pytest.raises(ValueError,match='gateway_headers'):
        PreviewRelay('https://approved.example.invalid',gateway_headers=headers)


def test_loopback_http_exception_does_not_allow_remote_cleartext():
    with pytest.raises(ValueError):
        PreviewRelay('http://example.invalid',allow_loopback_http=True)
