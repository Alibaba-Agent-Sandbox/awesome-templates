"""SDK-created sandbox controller: actual independently forwarded preview bytes.

This checks HTTP preview, not browser rendering or WebSocket/HMR support. The
caller owns sandbox deletion. Only nonce projects and servers started here are
removed; a pre-existing development server causes refusal.
"""
import asyncio
import secrets

import httpx


async def verify_forwarded(sandbox, *, workspace='/home/user/app'):
    if await sandbox.run('dev_status') != {'running': False}:
        raise RuntimeError('requires an exclusively owned idle preview sandbox')
    results = {}
    for kind, port, marker in [('next', 3000, 'ABX_NEXT_PREVIEW'), ('vite', 5173, 'ABX_VITE_PREVIEW')]:
        name = 'abx_e2e_forwarded_' + secrets.token_hex(12)
        path = workspace.rstrip('/') + '/' + name
        created = started = False
        if await sandbox.files.exists(path):
            raise RuntimeError('refuse pre-existing project')
        try:
            assert await sandbox.run('scaffold', kind=kind, path=name) == {'path': name, 'kind': kind}
            created = True
            assert await sandbox.run('dev_start', kind=kind, path=name) == {'port': port, 'kind': kind, 'running': True}
            started = True
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.get(sandbox.network.get_url(port) + '/')
            assert response.status_code == 200 and marker in response.text
            assert response.headers.get('content-type', '').split(';')[0].lower() == 'text/html'
            source_path = path + ('/app/page.js' if kind == 'next' else '/index.html')
            original = await sandbox.files.read(source_path)
            edited = 'ABX_EDITED_' + secrets.token_hex(12)
            assert marker in original
            await sandbox.files.write(source_path, original.replace(marker, edited))
            async with httpx.AsyncClient(timeout=120) as client:
                for _ in range(60):
                    updated = await client.get(sandbox.network.get_url(port) + '/')
                    if updated.status_code == 200 and edited in updated.text:
                        break
                    await asyncio.sleep(.5)
                else:
                    raise RuntimeError('independently forwarded preview did not serve edited source')
            results[kind] = {'port': port, 'independent_forwarded_http': True, 'independent_forwarded_source_edit': True,
                'html_attachment': response.headers.get('content-disposition', '').lower().startswith('attachment'),
                'browser_rendering': 'NOT_RUN', 'websocket_hmr': 'NOT_RUN'}
        finally:
            if started:
                assert await sandbox.run('dev_stop') == {'running': False}
            assert await sandbox.run('dev_status') == {'running': False}
            if created:
                await sandbox.files.remove(path)
                assert not await sandbox.files.exists(path)
            if kind in results:
                results[kind]['owned_server_and_project_cleanup'] = True
    return {'passed': len(results) == 2, 'previews': results}
