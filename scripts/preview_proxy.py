"""Explicit operator-local SDK preview relay; upstream HTTPS stays verified.

The borrowed sandbox and application remain caller-owned. Only the local listener,
HTTP/WebSocket clients and in-memory application cookies belong to this relay.
"""
from __future__ import annotations

import argparse
import asyncio
from contextlib import asynccontextmanager
import secrets
import ssl
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import getproxies, proxy_bypass

import aiohttp
from aiohttp import web
from multidict import CIMultiDict

_HOP = {'connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization',
        'te', 'trailer', 'transfer-encoding', 'upgrade'}


class PreviewRelay:
    """One fixed upstream, loopback binding and an ephemeral entry capability."""

    def __init__(self, upstream_url: str, *, _test_http: bool = False,
                 _ssl_context: ssl.SSLContext | None = None):
        parsed = urlsplit(upstream_url)
        if (parsed.scheme != 'https' and not (_test_http and parsed.scheme == 'http')
                or not parsed.hostname or parsed.username or parsed.password or parsed.fragment):
            raise ValueError('preview requires a verified HTTPS SDK endpoint')
        self.upstream = parsed
        self.proxy = None if parsed.hostname in ('127.0.0.1', 'localhost', '::1') or proxy_bypass(parsed.hostname) else getproxies().get(parsed.scheme)
        self.ssl_context = _ssl_context or ssl.create_default_context()
        if not self.ssl_context.check_hostname or self.ssl_context.verify_mode != ssl.CERT_REQUIRED:
            raise ValueError('upstream TLS hostname/certificate verification is required')
        self.token = secrets.token_urlsafe(24)
        self.entry = '/_abx_preview/' + self.token
        self.cookie = '_abx_preview_' + secrets.token_hex(8)
        self.session = self.runner = None
        self.sockets = set()
        self.port = 0
        self.html_attachment_normalized = False

    @property
    def origin(self) -> str:
        return 'http://127.0.0.1:' + str(self.port)

    @property
    def url(self) -> str:
        return self.origin + self.entry

    async def __aenter__(self):
        # Each relay has a separate RAM cookie jar. Browser/other local-port
        # cookies never reach the upstream and upstream cookies stay in RAM.
        self.session = aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar(unsafe=True),
            auto_decompress=False, trust_env=False, timeout=aiohttp.ClientTimeout(total=300))
        app = web.Application(client_max_size=16 * 1024**2)
        app.router.add_route('*', '/{path:.*}', self._handle)
        self.runner = web.AppRunner(app, access_log=None, shutdown_timeout=3)
        try:
            await self.runner.setup()
            site = web.TCPSite(self.runner, '127.0.0.1', 0)
            await site.start()
            address = self.runner.addresses[0]
            self.port = address[1]
            return self
        except BaseException:
            await self.__aexit__(None, None, None)
            raise

    async def __aexit__(self, *args):
        errors = []
        for socket in list(self.sockets):
            try:
                await socket.close()
            except Exception:
                errors.append('socket')
        if self.runner is not None:
            try:
                await self.runner.cleanup()
            except Exception:
                errors.append('listener')
        if self.session is not None:
            try:
                await self.session.close()
            except Exception:
                errors.append('HTTP client')
        if errors:
            raise RuntimeError('local preview cleanup not confirmed') from None

    def _target(self, request) -> str:
        raw = request.raw_path
        if raw == self.entry or raw.startswith(self.entry + '/') or raw.startswith(self.entry + '?'):
            raw = raw[len(self.entry):] or '/'
        path, _, query = raw.partition('?')
        # A path can never replace the selected upstream authority. Keep the
        # SDK's authentication query values; browser query cannot override them.
        private_query = parse_qsl(self.upstream.query, keep_blank_values=True)
        private_names = {name for name, _ in private_query}
        query_values = [(name, value) for name, value in parse_qsl(query, keep_blank_values=True)
                        if name not in private_names]
        base_path = self.upstream.path.rstrip('/')
        return urlunsplit((self.upstream.scheme, self.upstream.netloc,
                           base_path + '/' + path.lstrip('/'),
                           urlencode(query_values + private_query), ''))

    def _headers(self, request):
        excluded = _HOP | {'host', 'cookie', 'content-length', 'content-encoding'}
        excluded |= {word.strip().lower() for word in request.headers.get('Connection', '').split(',')}
        headers = CIMultiDict((key, value) for key, value in request.headers.items()
                              if key.lower() not in excluded and not key.lower().startswith('sec-websocket-'))
        if 'Origin' in headers:
            headers['Origin'] = self.upstream.scheme + '://' + self.upstream.netloc
        return headers

    async def _handle(self, request):
        if request.headers.get('Host') != '127.0.0.1:' + str(self.port):
            raise web.HTTPForbidden(text='local preview Host rejected')
        if request.headers.get('Origin') not in (None, self.origin):
            raise web.HTTPForbidden(text='local preview Origin rejected')
        entry = request.method == 'GET' and (request.path == self.entry or request.path.startswith(self.entry + '/'))
        authenticated = secrets.compare_digest(request.cookies.get(self.cookie, ''), self.token)
        if not entry and not authenticated:
            raise web.HTTPForbidden(text='open the private local preview entry first')
        if entry:
            # Give applications their canonical browser path before they derive
            # login cookie paths or absolute asset URLs from location.href.
            path = '/' + request.raw_path[len(self.entry):].lstrip('/')
            response = web.Response(status=303, headers={'Location':path, 'Cache-Control':'no-store'})
            response.set_cookie(self.cookie, self.token, httponly=True, samesite='Strict', path='/')
            return response
        target = self._target(request)
        headers = self._headers(request)
        try:
            if request.headers.get('Upgrade', '').lower() == 'websocket':
                return await self._websocket(request, target, headers)
            body = await request.read() if request.can_read_body else None
            async with self.session.request(request.method, target, data=body, headers=headers,
                    allow_redirects=False, ssl=self.ssl_context, proxy=self.proxy) as upstream:
                excluded = _HOP | {'set-cookie'}
                excluded |= {word.strip().lower() for word in upstream.headers.get('Connection', '').split(',')}
                outgoing = CIMultiDict((key, value) for key, value in upstream.headers.items() if key.lower() not in excluded)
                if 'Location' in outgoing:
                    location = urlsplit(outgoing['Location'])
                    if location.netloc:
                        if location.netloc != self.upstream.netloc or location.scheme not in ('http', 'https'):
                            raise web.HTTPBadGateway(text='redirect leaves the owned preview endpoint')
                        private_names = {key for key, _ in parse_qsl(self.upstream.query)}
                        query = urlencode([(key, value) for key, value in parse_qsl(location.query, keep_blank_values=True) if key not in private_names])
                        outgoing['Location'] = urlunsplit(('http', '127.0.0.1:' + str(self.port), location.path, query, ''))
                content_type = outgoing.get('Content-Type', '').split(';', 1)[0].strip().lower()
                disposition = outgoing.get('Content-Disposition', '').split(';', 1)[0].strip().lower()
                if content_type == 'text/html' and disposition == 'attachment':
                    outgoing.popall('Content-Disposition', None)
                    self.html_attachment_normalized = True
                response = web.StreamResponse(status=upstream.status, headers=outgoing)
                await response.prepare(request)
                async for chunk in upstream.content.iter_chunked(64 * 1024):
                    await response.write(chunk)
                await response.write_eof()
                return response
        except web.HTTPException:
            raise
        except (aiohttp.ClientError, asyncio.TimeoutError, ssl.SSLError):
            raise web.HTTPBadGateway(text='verified upstream preview transport failed') from None

    async def _websocket(self, request, target, headers):
        protocols = tuple(value.strip() for value in request.headers.get('Sec-WebSocket-Protocol', '').split(',') if value.strip())
        target = target.replace('https:', 'wss:', 1).replace('http:', 'ws:', 1)
        async with self.session.ws_connect(target, headers=headers, ssl=self.ssl_context,
                protocols=protocols, max_msg_size=8 * 1024**2, proxy=self.proxy) as upstream:
            client = web.WebSocketResponse(protocols=(upstream.protocol,) if upstream.protocol else (), max_msg_size=8 * 1024**2)
            await client.prepare(request)
            self.sockets.update((client, upstream))

            async def upstream_to_client():
                async for message in upstream:
                    if message.type == aiohttp.WSMsgType.TEXT:
                        await client.send_str(message.data)
                    elif message.type == aiohttp.WSMsgType.BINARY:
                        await client.send_bytes(message.data)
                await client.close()

            forwarding = asyncio.create_task(upstream_to_client())
            try:
                async for message in client:
                    if message.type == aiohttp.WSMsgType.TEXT:
                        await upstream.send_str(message.data)
                    elif message.type == aiohttp.WSMsgType.BINARY:
                        await upstream.send_bytes(message.data)
            finally:
                forwarding.cancel()
                await asyncio.gather(forwarding, return_exceptions=True)
                await upstream.close()
                self.sockets.difference_update((client, upstream))
            return client


@asynccontextmanager
async def sdk_preview(sandbox, *, remote_port: int = 8443):
    if type(remote_port) is not int or not 1 <= remote_port <= 65535:
        raise ValueError('remote_port must be an integer from1 to65535')
    async with PreviewRelay(sandbox.network.get_url(remote_port)) as relay:
        yield relay


async def main(sandbox_id, remote_port=8443):
    from agent_sandbox import ProviderSandbox
    sandbox = await ProviderSandbox.connect(sandbox_id)
    try:
        async with sdk_preview(sandbox, remote_port=remote_port) as relay:
            print('Open the private local preview:', relay.url, flush=True)
            await asyncio.Event().wait()
    finally:
        await sandbox.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sandbox-id', required=True, help='Caller-owned sandbox with authenticated IDE already running')
    parser.add_argument('--remote-port', type=int, default=8443, help='The caller-owned application port; default8443 for code-server')
    args = parser.parse_args()
    try:
        asyncio.run(main(args.sandbox_id, args.remote_port))
    except KeyboardInterrupt:
        pass
