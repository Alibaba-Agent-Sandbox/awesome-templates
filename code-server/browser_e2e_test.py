"""Verify an exclusively caller-owned IDE through the real browser and files SDK.

The caller owns the sandbox lifecycle. TLS remains enabled. This controller stops
only its IDE and removes its nonce file; it never destroys the caller's sandbox.
"""
from __future__ import annotations
import argparse
import asyncio
from contextlib import contextmanager
import json
import importlib.util
import os
from pathlib import Path
import re
import secrets
import shlex
import shutil
import ssl
import subprocess
import tempfile
import httpx
from playwright.async_api import async_playwright, TimeoutError as BrowserTimeout


class PreviewDomainError(RuntimeError):
    """The upstream domain prevents HTML rendering."""


@contextmanager
def browser_environment():
    """Import only operator-already-trusted CA roots into private Chromium NSS."""
    executable = shutil.which('certutil')
    if not executable:
        raise RuntimeError('certutil is required for the isolated browser trust store')
    trusted = set(ssl.create_default_context().get_ca_certs(binary_form=True))
    with tempfile.TemporaryDirectory(prefix='abx-ide-browser-') as private:
        home = Path(private)
        home.chmod(0o700)
        database = home / '.pki/nssdb'
        database.mkdir(parents=True, mode=0o700)
        def certutil(*args):
            result = subprocess.run([executable, *args], stdin=subprocess.DEVNULL,
                capture_output=True, timeout=30, env={
                    'PATH': os.environ.get('PATH', '/usr/bin:/bin'),
                    'HOME': str(home), 'LANG': 'C.UTF-8'})
            if result.returncode:
                raise RuntimeError('private browser trust-store configuration failed')
        certutil('-N', '--empty-password', '-d', 'sql:' + str(database))
        candidates = list(Path('/usr/local/share/ca-certificates').glob('*.crt'))
        for key in ['NODE_EXTRA_CA_CERTS', 'SSL_CERT_FILE', 'REQUESTS_CA_BUNDLE']:
            if os.environ.get(key):
                candidates.append(Path(os.environ[key]))
        imported = set()
        for filename in candidates:
            if not filename.is_file():
                continue
            for pem in re.findall(r'-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----', filename.read_text(), re.S):
                der = ssl.PEM_cert_to_DER_cert(pem)
                if der not in trusted or der in imported:
                    continue
                path = home / ('ca-' + str(len(imported)) + '.crt')
                path.write_text(pem + '\n')
                certutil('-A', '-d', 'sql:' + str(database), '-n',
                    'operator-trusted-' + str(len(imported)), '-t', 'C,,', '-i', str(path))
                imported.add(der)
        env = {key: os.environ[key] for key in ['PATH', 'LANG', 'LC_ALL', 'PLAYWRIGHT_BROWSERS_PATH'] if key in os.environ}
        env.update(HOME=str(home), XDG_CONFIG_HOME=str(home / 'config'), XDG_DATA_HOME=str(home / 'data'))
        yield env, len(imported)


async def verify_ui(sandbox, *, workspace='/home/user/app', preview_mode='direct') -> dict:
    if preview_mode not in ('direct', 'sdk-local'):
        raise ValueError('preview_mode must be direct or sdk-local')
    result = {'passed': False, 'preview_mode': preview_mode}
    started = False
    browser = playwright = None
    relay_context = relay = None
    relay_entered = False
    write_attempted = False
    name = 'abx_e2e_ide_ui_' + secrets.token_hex(12) + '.txt'
    path = workspace.rstrip('/') + '/' + name
    nonce, edited = secrets.token_hex(12), 'editor_' + secrets.token_hex(12)
    if await sandbox.files.exists(path):
        raise RuntimeError('refuse pre-existing controller artifact')
    with browser_environment() as (browser_env, ca_count):
        try:
            if await sandbox.run('code_server_status') != {'running': False}:
                raise RuntimeError('verification requires an exclusively owned sandbox with no running IDE')
            password = secrets.token_urlsafe(24)
            await sandbox.run('code_server_start', password=password, cwd=workspace)
            started = True
            url = sandbox.network.get_url(8443)
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                response = await client.get(url + '/?folder=' + workspace)
            attachment = response.headers.get('content-disposition', '').lower().startswith('attachment')
            content_type = response.headers.get('content-type', '').split(';')[0].lower()
            result['upstream_html_attachment'] = attachment and content_type == 'text/html'
            if result['upstream_html_attachment'] and preview_mode == 'direct':
                raise PreviewDomainError('preview domain forces HTML download; a supported custom domain is required')
            if preview_mode == 'sdk-local':
                # This is a normal explicit local HTTP/WS relay, not browser
                # response interception. The remote application stays real.
                spec = importlib.util.spec_from_file_location('abx_ide_preview_proxy', Path(__file__).resolve().parents[1] / 'scripts/preview_proxy.py')
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                relay_context = module.sdk_preview(sandbox)
                relay = await relay_context.__aenter__()
                relay_entered = True
                url = relay.url
                result.update(upstream_tls_verification_enabled=True,
                              browser_transport='http-loopback', local_proxy_loopback_only=True)
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=True, env=browser_env)
            page = await browser.new_page(locale='en-US')
            await page.goto(url + '/?folder=' + workspace, wait_until='domcontentloaded', timeout=120000)
            await page.locator('input[name="password"]').fill(password)
            await page.locator('input[type="submit"],button[type="submit"]').click()
            await page.locator('.monaco-workbench').wait_for(state='visible', timeout=180000)
            result.update(workbench_javascript_loaded=True, tls_verification_enabled=True,
                operator_trusted_cas_imported=ca_count)
            initial_trust = page.get_by_role('button', name='Yes, I trust the authors', exact=False)
            try:
                await initial_trust.first.wait_for(state='visible', timeout=4000)
                await initial_trust.first.click()
            except BrowserTimeout:
                pass
            await page.keyboard.press('Control+Shift+P')
            quick = page.locator('.quick-input-box input')
            await quick.wait_for(state='visible')
            await quick.fill('>Terminal: Create New Terminal')
            command_row = page.locator('.quick-input-list .monaco-list-row').filter(has_text='Create New Terminal').first
            await command_row.wait_for(state='visible')
            await command_row.click()
            trust = page.get_by_role('button', name='Trust Folder & Continue', exact=True)
            try:
                await trust.wait_for(state='visible', timeout=10000)
                await trust.click()
            except BrowserTimeout:
                pass
            terminal = page.locator('textarea.xterm-helper-textarea').last
            await terminal.wait_for(state='attached', timeout=60000)
            await terminal.focus()
            command = 'printf %s ' + shlex.quote(nonce) + ' > ' + shlex.quote(path)
            for attempt in range(3):
                await terminal.press('Control+c')
                await page.wait_for_timeout(500)
                write_attempted = True
                await page.keyboard.insert_text(command)
                await terminal.press('Enter')
                for _ in range(20):
                    if await sandbox.files.exists(path) and await sandbox.files.read(path) == nonce:
                        break
                    await asyncio.sleep(.25)
                else:
                    continue
                result.update(terminal_websocket_file_readback=True, terminal_write_attempts=attempt + 1)
                break
            else:
                raise RuntimeError('terminal WebSocket write did not produce expected bytes')
            await page.keyboard.press('Control+p')
            await quick.wait_for(state='visible')
            await quick.fill(name)
            file_row = page.locator('.quick-input-list .monaco-list-row').filter(has_text=name).first
            await file_row.wait_for(state='visible')
            await file_row.click()
            editor = page.locator('.monaco-editor .view-lines').filter(has_text=nonce).first
            await editor.wait_for(state='visible', timeout=60000)
            await editor.click()
            await page.keyboard.press('Control+a')
            await page.keyboard.insert_text(edited)
            await page.keyboard.press('Control+s')
            for _ in range(60):
                if await sandbox.files.read(path) == edited:
                    break
                await asyncio.sleep(.5)
            else:
                raise RuntimeError('actual browser editor save did not produce expected bytes')
            result['browser_editor_independent_file_readback'] = True
        finally:
            errors = []
            for resource in [browser, playwright]:
                if resource is None:
                    continue
                try:
                    if resource is browser:
                        await resource.close()
                    else:
                        await resource.stop()
                except Exception:
                    errors.append('browser teardown')
            if relay_entered:
                try:
                    await relay_context.__aexit__(None, None, None)
                    result['owned_local_proxy_closed'] = True
                    result['upstream_html_attachment_normalized'] = relay.html_attachment_normalized
                except Exception:
                    errors.append('owned local proxy cleanup')
            if started:
                try:
                    await sandbox.run('code_server_stop')
                    assert await sandbox.run('code_server_status') == {'running': False}
                    result['owned_ide_stop_confirmed'] = True
                except Exception:
                    errors.append('owned IDE cleanup')
            try:
                if write_attempted and await sandbox.files.exists(path):
                    await sandbox.files.remove(path)
                result['owned_ui_file_absence'] = not await sandbox.files.exists(path)
                assert result['owned_ui_file_absence']
            except Exception:
                errors.append('owned artifact cleanup')
            if errors:
                raise RuntimeError('browser verification cleanup not confirmed') from None
    result['passed'] = all(result.get(key) is True for key in [
        'workbench_javascript_loaded', 'tls_verification_enabled', 'terminal_websocket_file_readback',
        'browser_editor_independent_file_readback', 'owned_ide_stop_confirmed', 'owned_ui_file_absence'])
    if preview_mode == 'sdk-local':
        result['passed'] = result['passed'] and all(result.get(key) is True for key in [
            'upstream_tls_verification_enabled', 'local_proxy_loopback_only', 'owned_local_proxy_closed'])
    return result


async def main(sandbox_id, preview_mode='direct'):
    from agent_sandbox.api.sandbox import Sandbox
    sandbox = await Sandbox.connect(sandbox_id)
    try:
        try:
            result = await verify_ui(sandbox, preview_mode=preview_mode)
        except Exception as exc:
            result = {'passed': False, 'error_type': type(exc).__name__}
            if isinstance(exc, PreviewDomainError):
                result['blocked_reason'] = 'The preview domain forces HTML download; configure a supported custom domain.'
        print(json.dumps(result, sort_keys=True))
        return 0 if result['passed'] else 1
    finally:
        await sandbox.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sandbox-id', required=True, help='An exclusively caller-owned sandbox; the controller does not delete it')
    parser.add_argument('--preview-mode', choices=('direct', 'sdk-local'), default='direct')
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main(args.sandbox_id, args.preview_mode)))
