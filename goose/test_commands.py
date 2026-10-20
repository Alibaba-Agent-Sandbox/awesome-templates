"""Real native CLI/protocol/process tests; synthetic HTTP is not model acceptance."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import pytest
sys.path.insert(0, str(Path(__file__).parent))
spec = importlib.util.spec_from_file_location('goose_commands_under_test', Path(__file__).with_name('commands.py'))
commands = importlib.util.module_from_spec(spec)
spec.loader.exec_module(commands)
_run_process = commands._run_process


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    monkeypatch.setenv('WORKSPACE', str(tmp_path))
    # Local diagnostics may point at an independently verified official binary.
    binary = os.environ.get('GOOSE_TEST_BINARY')
    if binary:
        monkeypatch.setenv('GOOSE_BINARY', binary)
    return tmp_path


def test_actual_pin_and_read_only_diagnostic(runtime, monkeypatch):
    for name in ('GOOSE_API_KEY', 'GOOSE_BASE_URL', 'GOOSE_MODEL'):
        monkeypatch.delenv(name, raising=False)
    home = runtime / 'caller-home'
    home.mkdir()
    (home / 'keep').write_text('untouched')
    monkeypatch.setenv('HOME', str(home))
    assert commands.goose_version() == '1.54.0'
    assert commands.goose_setup_check() == {'installed': True, 'version': '1.54.0', 'api_key_set': False, 'base_url_set': False, 'model_set': False}
    assert sorted(p.name for p in home.iterdir()) == ['keep']
    assert (home / 'keep').read_text() == 'untouched'


@pytest.mark.parametrize('allow_tools', [False, True])
def test_actual_goose_compatible_protocol_literal_stdin_and_tool_permission(runtime, monkeypatch, allow_tools):
    seen = []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def do_GET(self):
            data = json.dumps({'data': [{'id': 'fixture-model', 'object': 'model', 'owned_by': 'fixture'}]}).encode()
            self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers(); self.wfile.write(data)
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            seen.append(body)
            if body.get('stream'):
                first = {'id': 'fixture', 'object': 'chat.completion.chunk', 'created': 0, 'model': 'fixture-model', 'choices': [{'index': 0, 'delta': {'role': 'assistant', 'content': 'LOCAL_GOOSE_OK'}, 'finish_reason': None}]}
                last = {'id': 'fixture', 'object': 'chat.completion.chunk', 'created': 0, 'model': 'fixture-model', 'choices': [{'index': 0, 'delta': {}, 'finish_reason': 'stop'}]}
                data = ('data: ' + json.dumps(first) + '\n\ndata: ' + json.dumps(last) + '\n\ndata: [DONE]\n\n').encode(); mime = 'text/event-stream'
            else:
                data = json.dumps({'id': 'fixture', 'object': 'chat.completion', 'created': 0, 'model': 'fixture-model', 'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': 'LOCAL_GOOSE_OK'}, 'finish_reason': 'stop'}], 'usage': {'prompt_tokens': 1, 'completion_tokens': 1, 'total_tokens': 2}}).encode(); mime = 'application/json'
            self.send_response(200); self.send_header('Content-Type', mime); self.end_headers(); self.wfile.write(data)
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    monkeypatch.setenv('GOOSE_API_KEY', 'synthetic-local-key')
    monkeypatch.setenv('GOOSE_BASE_URL', 'http://127.0.0.1:' + str(server.server_port) + '/v1')
    monkeypatch.setenv('GOOSE_MODEL', 'fixture-model')
    try:
        result = commands.goose('Reply LOCAL_GOOSE_OK. Literal: $(touch NEVER_SHELL)', allow_tools=allow_tools, command_timeout=60)
        assert result['exit_code'] == 0 and 'LOCAL_GOOSE_OK' in result['stdout']
        assert seen and any('$(touch NEVER_SHELL)' in str(m) for m in seen[-1]['messages'])
        names = [tool['function']['name'] for tool in seen[-1].get('tools', [])]
        if allow_tools:
            assert {'edit', 'read_image', 'shell', 'tree', 'write'} <= set(names)
        else:
            assert names == []
        assert not (runtime / 'NEVER_SHELL').exists()
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=5)


def test_required_configuration_refuses_before_native_execution(runtime, monkeypatch):
    for name in ('GOOSE_API_KEY', 'GOOSE_BASE_URL', 'GOOSE_MODEL'):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(commands, '_binary', lambda: pytest.fail('missing config must not execute CLI'))
    with pytest.raises(RuntimeError, match='are required'):
        commands.goose('hello')


def test_argument_path_and_endpoint_guards(runtime, monkeypatch):
    for action in [lambda: commands.goose(''), lambda: commands.goose('x\0'), lambda: commands.goose('x', allow_tools='true'), lambda: commands.goose('x', command_timeout=False), lambda: commands.goose('x', command_timeout=1801)]:
        with pytest.raises(ValueError): action()
    for name, value in [('GOOSE_API_KEY', 'synthetic-key'), ('GOOSE_MODEL', 'fixture-model'), ('GOOSE_BASE_URL', 'https://user:pass@example.invalid/v1')]:
        monkeypatch.setenv(name, value)
    with pytest.raises(ValueError, match='without credentials'):
        commands.goose('x')
    with pytest.raises(ValueError, match='WORKSPACE'):
        commands._workspace('..')
    (runtime / 'escape').symlink_to('/tmp', target_is_directory=True)
    with pytest.raises(ValueError, match='WORKSPACE'):
        commands._workspace('escape')


def test_child_environment_excludes_cloud_server_keys_and_loader_options(monkeypatch):
    monkeypatch.setenv('ALICLOUD_ACCESS_KEY_SECRET', 'synthetic-cloud')
    monkeypatch.setenv('ABX_SERVER_TOKEN', 'synthetic-server')
    monkeypatch.setenv('LD_PRELOAD', 'synthetic-loader')
    env = commands._environment('/tmp/synthetic-private-home')
    assert not any(name in env for name in ['ALICLOUD_ACCESS_KEY_SECRET', 'ABX_SERVER_TOKEN', 'LD_PRELOAD'])
    assert env['HOME'] == '/tmp/synthetic-private-home' and env['CONTEXT_FILE_NAMES'] == '[]'


@pytest.mark.parametrize('status', [0, 7])
def test_real_redirected_descendant_cleanup(runtime, status):
    marker = runtime / 'leak'
    child = 'import pathlib,time;time.sleep(.3);pathlib.Path(' + repr(str(marker)) + ').write_text("leaked")'
    parent = 'import subprocess,sys;subprocess.Popen([sys.executable,"-c",' + repr(child) + '],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,stdin=subprocess.DEVNULL);sys.exit(' + str(status) + ')'
    code, _, _ = _run_process([sys.executable, '-c', parent], cwd=str(runtime), timeout=5)
    assert code == status
    time.sleep(.4)
    assert not marker.exists()


def test_real_output_limit_and_timeout_cleanup(runtime):
    code = 'import os\nwhile True: os.write(1,b"x"*65536)'
    with pytest.raises(RuntimeError, match='output exceeded'):
        _run_process([sys.executable, '-c', code], cwd=str(runtime), timeout=5)
    marker = runtime / 'late'
    code = 'import time,pathlib;time.sleep(.4);pathlib.Path(' + repr(str(marker)) + ').write_text("leaked")'
    with pytest.raises(RuntimeError, match='timed out'):
        _run_process([sys.executable, '-c', code], cwd=str(runtime), timeout=.05)
    time.sleep(.5)
    assert not marker.exists()
