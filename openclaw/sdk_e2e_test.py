#!/usr/bin/env python3
"""Borrow a fresh owned sandbox; verify real SDK gateway lifecycle and cleanup.

This controller does not destroy its caller's sandbox or call a model. It owns
only its explicit port-9010 command server and that server's gateway/state.
"""
import argparse
import asyncio
import ipaddress
import json
import secrets
import shlex

import httpx


def probe_succeeded(endpoint, response):
    """The pinned gateway has distinct liveness and readiness JSON contracts."""
    if response.status_code != 200:
        return False
    try:
        payload = response.json()
    except ValueError:
        return False
    field = 'ready' if endpoint == 'readyz' else 'ok'
    return isinstance(payload, dict) and payload.get(field) is True


async def observe_owned_ingress(sb):
    """Observe our nonce request's kernel peer, never trust forwarded header values."""
    nonce = secrets.token_urlsafe(24)
    source = '''import http.server,json,os,threading
class Handler(http.server.BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  if self.path!='/'+os.environ['ABX_GATEWAY_PROBE_NONCE']:
   self.send_error(404);return
  body=json.dumps({'peer':self.client_address[0]}).encode()
  self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
  threading.Thread(target=self.server.shutdown,daemon=True).start()
server=http.server.ThreadingHTTPServer(('0.0.0.0',9012),Handler)
timer=threading.Timer(45,server.shutdown);timer.daemon=True;timer.start()
try:server.serve_forever(poll_interval=.1)
finally:server.server_close();timer.cancel()
'''
    stream = await sb.commands.start('python3 -I -c ' + shlex.quote(source),
                                      env={'ABX_GATEWAY_PROBE_NONCE': nonce}, timeout=60)
    entry = {'pid': None, 'exited': False}
    ready = asyncio.Event()

    async def consume():
        try:
            async for item in stream:
                if item.pid:
                    entry['pid'] = item.pid
                    ready.set()
                if getattr(item, 'exit_code', None) is not None:
                    entry['exited'] = True
        finally:
            ready.set()

    drain = asyncio.create_task(consume())
    try:
        await asyncio.wait_for(ready.wait(), 120)
        if not entry['pid']:
            raise RuntimeError('owned transport probe returned no process identity')
        async with httpx.AsyncClient(timeout=10) as client:
            for _ in range(20):
                try:
                    response = await client.get(sb.network.get_url(9012).rstrip('/') + '/' + nonce)
                    response.raise_for_status()
                    peer = ipaddress.ip_address(response.json()['peer'])
                    if peer.is_unspecified or peer.is_multicast:
                        raise ValueError('kernel peer is not unicast')
                    break
                except httpx.HTTPError:
                    await asyncio.sleep(.3)
            else:
                raise RuntimeError('owned ingress observation failed')
        await asyncio.wait_for(drain, 15)
        # This explicit test configuration is for our own observed ingress only.
        # The product never derives trusted proxies from request headers.
        return str(peer) + ('/32' if peer.version == 4 else '/128'), {
            'peer_loopback': peer.is_loopback, 'peer_private': peer.is_private,
            'peer_global': peer.is_global, 'peer_version': peer.version}
    finally:
        if entry['pid'] and not entry['exited']:
            await sb.commands.kill(entry['pid'])
        drain.cancel()
        await asyncio.gather(drain, return_exceptions=True)
        await stream.cancel()


async def verify(sb, diagnostics=None):
    report = {"passed": False, "model_acceptance": "NOT_APPLICABLE_GATEWAY_ONLY"}
    owned = {"stream": None, "pid": None, "drain": None, "exited": False}
    server = None
    gateway_attempted = False
    baseline_states = None

    async def states():
        items = await sb.files.list('/tmp')
        return {item.name for item in items if item.name.startswith('abx-openclaw-')}

    async def listeners_absent():
        source = "import socket,json;result=[]\nfor port in [9010,9012,18789]:\n s=socket.socket();s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)\n try:s.bind(('0.0.0.0',port));result.append(True)\n except OSError:result.append(False)\n finally:s.close()\nprint(json.dumps(result))"
        result = await sb.commands.run('python3 -I -c ' + shlex.quote(source), timeout=15)
        return result.exit_code == 0 and json.loads(result.stdout) == [True, True, True]

    # Refuse occupied caller ports before any mutation; never reclaim a port.
    if not await listeners_absent():
        raise RuntimeError('fresh sandbox requires free ports 9010, 9012 and 18789')
    baseline_states = await states()
    token = secrets.token_urlsafe(32)
    gateway_token = secrets.token_urlsafe(32)
    try:
        trusted_proxy, transport = await observe_owned_ingress(sb)
        report['observed_forwarded_transport'] = transport
        env = {'PATH': '/opt/node/current/bin:/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin',
               'HOME': '/home/user', 'WORKSPACE': '/home/user/app',
               'ABX_SERVER_TOKEN': token, 'OPENCLAW_GATEWAY_TOKEN': gateway_token,
               'OPENCLAW_TRUSTED_PROXIES': trusted_proxy}
        owned['stream'] = await sb.commands.start(
            'agent-sandbox-server serve --port 9010 --commands /home/user/app/commands.py',
            env=env, timeout=600)
        ready = asyncio.Event()

        async def consume():
            try:
                async for item in owned['stream']:
                    if item.pid:
                        owned['pid'] = item.pid
                        ready.set()
                    if getattr(item, 'exit_code', None) is not None:
                        owned['exited'] = True
            finally:
                ready.set()

        owned['drain'] = asyncio.create_task(consume())
        await asyncio.wait_for(ready.wait(), 120)
        if not owned['pid']:
            raise RuntimeError('owned command server did not return its process identity')
        server = sb.server_at(9010, token=token)
        for _ in range(60):
            try:
                if await server.health():
                    break
            except Exception:
                pass
            await asyncio.sleep(1)
        else:
            raise RuntimeError('owned command server did not become ready')
        initial = await server.commands.run('gateway_status')
        assert initial.get('running') is False and initial.get('owned') is False
        report['initial_owned_status_stopped'] = True
        gateway_attempted = True
        started = await server.commands.run('gateway_start', port=18789, bind='lan',
                                            command_timeout=90, timeout=120)
        assert started.get('running') is True and started.get('healthy') is True
        report['sdk_native_authenticated_start'] = True
        health = await server.commands.run('gateway_health', command_timeout=30, timeout=45)
        assert health.get('healthy') is True
        report['sdk_native_authenticated_rpc'] = True
        status = await server.commands.run('gateway_status')
        assert status.get('running') is True and status.get('owned') is True
        report['gateway_survives_start_response'] = True
        async with httpx.AsyncClient(timeout=20) as client:
            base = sb.network.get_url(18789).rstrip('/')
            for endpoint in ['healthz', 'readyz']:
                for _ in range(60):
                    response = await client.get(base + '/' + endpoint)
                    report['external_' + endpoint + '_last_status'] = response.status_code
                    if probe_succeeded(endpoint, response):
                        break
                    await asyncio.sleep(1)
                else:
                    raise AssertionError('forwarded gateway ' + endpoint + ' failed its native contract')
                report['external_sdk_forwarded_' + endpoint] = True
        stopped = await server.commands.run('gateway_stop', command_timeout=10, timeout=30)
        assert stopped.get('running') is False
        report['sdk_native_stop'] = True
        status = await server.commands.run('gateway_status')
        assert status.get('running') is False and status.get('owned') is False
        report['sdk_status_stopped'] = True
        report['passed'] = True
    finally:
        cleanup = True
        if server:
            if gateway_attempted:
                try:
                    await server.commands.run('gateway_stop', command_timeout=10, timeout=30)
                except Exception:
                    cleanup = False
            try:
                await server.aclose()
            except Exception:
                cleanup = False
        if owned['pid'] and not owned['exited']:
            try:
                await sb.commands.kill(owned['pid'])
            except Exception:
                cleanup = False
        if owned['drain']:
            owned['drain'].cancel()
            await asyncio.gather(owned['drain'], return_exceptions=True)
        if owned['stream']:
            try:
                await owned['stream'].cancel()
            except Exception:
                cleanup = False
        absent = False
        for _ in range(10):
            if await listeners_absent():
                absent = True
                break
            await asyncio.sleep(.2)
        report['owned_cleanup_ack'] = cleanup
        report['owned_listeners_absent'] = absent
        report['owned_state_directories_absent'] = await states() == baseline_states
        if diagnostics is not None:
            diagnostics.update(report)
        if not all([cleanup, absent, report['owned_state_directories_absent']]):
            raise RuntimeError('owned gateway/process/state cleanup not independently confirmed')
    return report


async def main():
    from agent_sandbox import ProviderSandbox
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sandbox-id', required=True)
    args = parser.parse_args()
    sb = await ProviderSandbox.connect(args.sandbox_id)
    try:
        print(json.dumps(await verify(sb), indent=2))
    finally:
        await sb.close()


if __name__ == '__main__':
    asyncio.run(main())
