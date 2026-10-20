"""Actual local browser/PTY/editor tests; the file observer is not the cloud SDK."""
import asyncio
import importlib.util
import os
from pathlib import Path
import pytest


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_real_local_browser_terminal_editor_roundtrip(tmp_path, monkeypatch):
    commands = load('local_browser_commands', 'commands.py')
    controller = load('local_browser_controller', 'browser_e2e_test.py')
    monkeypatch.setenv('WORKSPACE', str(tmp_path))
    monkeypatch.setenv('OPENAI_API_KEY', 'synthetic-not-for-browser')
    class Files:
        async def exists(self, path): return Path(path).exists()
        async def read(self, path): return Path(path).read_text()
        async def remove(self, path): Path(path).unlink()
    class Network:
        def get_url(self, port): return 'http://127.0.0.1:' + str(port)
    class LocalAdapter:
        files = Files()
        network = Network()
        async def run(self, name, **kwargs):
            return await asyncio.to_thread(getattr(commands, name), **kwargs)
    result = asyncio.run(controller.verify_ui(LocalAdapter(), workspace=str(tmp_path)))
    assert result['passed'] and result['workbench_javascript_loaded']
    assert result['terminal_websocket_file_readback'] and result['browser_editor_independent_file_readback']
    assert result['owned_ide_stop_confirmed'] and result['owned_ui_file_absence']
    assert list(tmp_path.iterdir()) == []


def test_private_browser_environment_filters_credentials_and_preserves_operator_home(monkeypatch):
    controller = load('browser_environment_controller', 'browser_e2e_test.py')
    monkeypatch.setenv('ALICLOUD_ACCESS_KEY_SECRET', 'synthetic-cloud-secret')
    monkeypatch.setenv('OPENAI_API_KEY', 'synthetic-model-secret')
    before = os.environ.get('HOME')
    with controller.browser_environment() as (env, _):
        assert 'ALICLOUD_ACCESS_KEY_SECRET' not in env and 'OPENAI_API_KEY' not in env
        assert env['HOME'] != before
        home = Path(env['HOME'])
        assert home.is_dir() and home.stat().st_mode & 0o777 == 0o700
    assert not home.exists() and os.environ.get('HOME') == before


def test_missing_trust_tool_blocks_before_ide_mutation(monkeypatch):
    controller = load('missing_trust_controller', 'browser_e2e_test.py')
    monkeypatch.setattr(controller.shutil, 'which', lambda _: None)
    class Files:
        async def exists(self, path): return False
    class Target:
        files = Files()
        async def run(self, *args, **kwargs): raise AssertionError('must fail before IDE mutation')
    with pytest.raises(RuntimeError, match='certutil'):
        asyncio.run(controller.verify_ui(Target()))


def test_browser_teardown_error_still_stops_actual_owned_ide(tmp_path, monkeypatch):
    commands = load('teardown_local_commands', 'commands.py')
    controller = load('teardown_browser_controller', 'browser_e2e_test.py')
    monkeypatch.setenv('WORKSPACE', str(tmp_path))
    class Files:
        async def exists(self, path): return Path(path).exists()
        async def remove(self, path): Path(path).unlink()
    class Network:
        def get_url(self, port): return 'http://127.0.0.1:' + str(port)
    class LocalAdapter:
        files = Files()
        network = Network()
        async def run(self, name, **kwargs):
            return await asyncio.to_thread(getattr(commands, name), **kwargs)
    class Page:
        async def goto(self, *args, **kwargs): raise RuntimeError('synthetic navigation failure')
    class Browser:
        async def new_page(self, **kwargs): return Page()
        async def close(self): raise RuntimeError('synthetic browser teardown failure')
    class Driver:
        chromium = None
        def __init__(self): self.chromium = self
        async def start(self): return self
        async def launch(self, **kwargs): return Browser()
        async def stop(self): pass
    monkeypatch.setattr(controller, 'async_playwright', Driver)
    with pytest.raises(RuntimeError, match='cleanup not confirmed'):
        asyncio.run(controller.verify_ui(LocalAdapter(), workspace=str(tmp_path)))
    assert commands.code_server_status() == {'running': False}
    assert list(tmp_path.iterdir()) == []


def test_forced_attachment_blocks_before_browser_and_stops_owned_ide(monkeypatch):
    from contextlib import contextmanager
    import httpx
    controller = load('attachment_preview_controller', 'browser_e2e_test.py')
    @contextmanager
    def environment(): yield {}, 0
    monkeypatch.setattr(controller, 'browser_environment', environment)
    monkeypatch.setattr(controller, 'async_playwright', lambda: pytest.fail('blocked HTML must not launch a browser'))
    original = controller.httpx.AsyncClient
    def transport(request):
        return httpx.Response(200, headers={'content-type': 'text/html', 'content-disposition': 'attachment'}, text='<html>test</html>')
    monkeypatch.setattr(controller.httpx, 'AsyncClient', lambda **kwargs: original(transport=httpx.MockTransport(transport), **kwargs))
    class Files:
        async def exists(self, path): return False
    class Network:
        def get_url(self, port): return 'https://example.invalid'
    class Target:
        files = Files()
        network = Network()
        running = False
        stopped = False
        async def run(self, name, **kwargs):
            if name == 'code_server_status': return {'running': self.running}
            if name == 'code_server_start': self.running = True
            if name == 'code_server_stop': self.running = False; self.stopped = True
    target = Target()
    with pytest.raises(controller.PreviewDomainError, match='forces HTML download'):
        asyncio.run(controller.verify_ui(target))
    assert target.stopped and not target.running
