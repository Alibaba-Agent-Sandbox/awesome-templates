"""Behavioral regressions for the coding tool protocol, errors and key privacy."""
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import httpx
import pytest

spec = importlib.util.spec_from_file_location('deepseek_template', Path(__file__).with_name('commands.py'))
commands = importlib.util.module_from_spec(spec)
spec.loader.exec_module(commands)


def test_real_file_tools_and_path_traversal(tmp_path):
    assert commands._tool('write_file', {'path': 'src/a.py', 'content': 'answer = 42\n'}, tmp_path, 10) == 'written'
    assert commands._tool('read_file', {'path': 'src/a.py'}, tmp_path, 10) == 'answer = 42\n'
    assert json.loads(commands._tool('list_files', {'path': 'src'}, tmp_path, 10)) == ['a.py']
    (tmp_path/'outside').symlink_to(tmp_path.parent, target_is_directory=True)
    for name in ['../escape', 'outside/escape']:
        with pytest.raises(ValueError, match='inside cwd'):
            commands._tool('write_file', {'path': name, 'content': 'bad'}, tmp_path, 10)


def test_shell_executes_and_strips_credentials(monkeypatch, tmp_path):
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'synthetic-private-key')
    result = json.loads(commands._tool('run_shell', {'command': 'printf "$DEEPSEEK_API_KEY"; exit 3'}, tmp_path, 10))
    assert result['stdout'] == '' and result['exit_code'] == 3


def test_tool_round_trip_writes_real_artifact(monkeypatch, tmp_path):
    monkeypatch.setenv('WORKSPACE', str(tmp_path))
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'synthetic-private-key')
    sent = []
    def handler(request):
        body = json.loads(request.content)
        sent.append(body)
        if len(sent) == 1:
            message = {'role': 'assistant', 'content': None, 'tool_calls': [{'id': 'tool-1', 'type': 'function', 'function': {
                'name': 'write_file', 'arguments': json.dumps({'path': 'new.txt', 'content': 'real artifact'})}}]}
        else:
            assert body['messages'][-1] == {'role': 'tool', 'tool_call_id': 'tool-1', 'content': 'written'}
            message = {'role': 'assistant', 'content': 'done'}
        return httpx.Response(200, json={'choices': [{'message': message}]})
    client_class = httpx.Client
    monkeypatch.setattr(commands.httpx, 'Client', lambda **kwargs: client_class(transport=httpx.MockTransport(handler), **kwargs))
    assert json.loads(commands._agent_loop('fix files')) == {'content': 'done', 'tool_calls': 1}
    assert (tmp_path/'new.txt').read_text() == 'real artifact'
    assert sent[0]['model'] == 'deepseek-flash'


def test_api_failure_omits_body_and_key(monkeypatch, tmp_path):
    monkeypatch.setenv('WORKSPACE', str(tmp_path))
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'synthetic-private-key')
    client_class = httpx.Client
    monkeypatch.setattr(commands.httpx, 'Client', lambda **kw: client_class(transport=httpx.MockTransport(
        lambda r: httpx.Response(401, text='synthetic-private-key private-prompt')), **kw))
    with pytest.raises(RuntimeError) as exc:
        commands._agent_loop('private-prompt')
    assert 'synthetic-private-key' not in str(exc.value) and 'private-prompt' not in str(exc.value)


@pytest.mark.parametrize('kwargs', [{'prompt':' '}, {'max_turns':0}, {'max_turns':101}, {'command_timeout':0}, {'command_timeout':1801}])
def test_rejects_invalid_arguments(kwargs):
    with pytest.raises(ValueError):
        commands.deepseek(**({'prompt':'test'} | kwargs))


def test_missing_key_guard(monkeypatch, tmp_path):
    monkeypatch.setenv('WORKSPACE', str(tmp_path))
    monkeypatch.delenv('DEEPSEEK_API_KEY', raising=False)
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    with pytest.raises(RuntimeError, match='required'):
        commands.deepseek('test')


def test_compatibility_run_is_argv_safe_and_fails(monkeypatch, tmp_path):
    monkeypatch.setenv('WORKSPACE', str(tmp_path))
    (tmp_path/'main.py').write_text('print("compatibility")\n')
    assert commands.run() == 'compatibility\n'
    (tmp_path/'main.py').write_text('raise RuntimeError("expected failure")\n')
    with pytest.raises(RuntimeError, match='expected failure'):
        commands.run()


def test_tool_loop_exhaustion_is_execution_error(monkeypatch, tmp_path):
    monkeypatch.setenv('WORKSPACE', str(tmp_path))
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'synthetic-private-key')
    client_class = httpx.Client
    message = {'role':'assistant', 'content':None, 'tool_calls':[{'id':'tool-1','type':'function',
        'function':{'name':'unknown_tool','arguments':'{}'}}]}
    monkeypatch.setattr(commands.httpx, 'Client', lambda **kw: client_class(transport=httpx.MockTransport(
        lambda r: httpx.Response(200, json={'choices':[{'message':message}]})), **kw))
    with pytest.raises(RuntimeError, match='max_turns'):
        commands._agent_loop('keep working', max_turns=2)


def test_worker_deadline_kills_descendants_without_prompt_in_error(monkeypatch, tmp_path):
    import subprocess
    import time
    monkeypatch.setenv('WORKSPACE', str(tmp_path))
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'synthetic-private-key')
    marker = tmp_path/'survived'
    child = 'import time;time.sleep(2);open(' + repr(str(marker)) + ',"w").write("bad")'
    worker = 'import sys,subprocess,time;subprocess.Popen([sys.executable,"-c",' + repr(child) + ']);time.sleep(30)'
    original = subprocess.Popen
    monkeypatch.setattr(commands.subprocess, 'Popen', lambda argv, **kw: original([sys.executable,'-c',worker], **kw))
    with pytest.raises(RuntimeError, match='timed out') as exc:
        commands.deepseek('private request', command_timeout=1)
    assert 'private request' not in str(exc.value)
    time.sleep(1.2)
    assert not marker.exists()


@pytest.mark.parametrize("exit_code", [0, 7])
def test_leader_exit_cleans_owned_descendants(monkeypatch, tmp_path, exit_code):
    import subprocess
    import time
    monkeypatch.setenv("WORKSPACE", str(tmp_path))
    marker = tmp_path / "escaped-cleanup"
    child = f"import time;time.sleep(1.5);open({str(marker)!r},'w').write('bad')"
    leader = ("import subprocess,sys;subprocess.Popen([sys.executable,'-c'," + repr(child) +
              "],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);"
              "print('leader-output',flush=True);sys.exit(" + str(exit_code) + ")")
    code, stdout, stderr = commands._run_process([sys.executable, "-c", leader], cwd=str(tmp_path), timeout=5)
    assert code == exit_code and stdout == "leader-output\n" and stderr == ""
    time.sleep(1.7)
    assert not marker.exists()


def test_runner_drains_large_stdout_and_stderr_without_deadlock(tmp_path):
    code, stdout, stderr = commands._run_process([sys.executable, "-c",
        "import sys;sys.stdout.write('x'*200000);sys.stderr.write('y'*200000)"], cwd=str(tmp_path), timeout=5)
    assert code == 0 and stdout == "x"*200000 and stderr == "y"*200000


@pytest.mark.parametrize("outer_deadline", [False, True])
def test_actual_worker_deadline_unwinds_active_shell_and_its_descendants(monkeypatch, tmp_path, outer_deadline):
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    import threading
    import time
    monkeypatch.setenv('WORKSPACE', str(tmp_path))
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'synthetic-private-key')
    marker = tmp_path/'shell-descendant-survived'
    child = f"import time;time.sleep(2);open({str(marker)!r},'w').write('bad')"
    tool_code = 'import subprocess,sys,time;subprocess.Popen([sys.executable,"-c",'+repr(child)+']);time.sleep(30)'
    import shlex
    shell = shlex.quote(sys.executable)+' -c '+shlex.quote(tool_code)
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            self.rfile.read(int(self.headers['Content-Length']))
            message = {'role':'assistant','content':None,'tool_calls':[{'id':'shell-1','type':'function',
                       'function':{'name':'run_shell','arguments':json.dumps({'command':shell})}}]}
            body=json.dumps({'choices':[{'message':message}]}).encode()
            self.send_response(200);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(('127.0.0.1',0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True);thread.start()
    monkeypatch.setenv('DEEPSEEK_BASE_URL',f'http://127.0.0.1:{server.server_port}')
    try:
        if outer_deadline:
            with pytest.raises(RuntimeError, match='timed out'):
                commands.deepseek('test owner cancellation', command_timeout=1)
        else:
            # Let the worker's own deadline expire before its owner budget.
            code, stdout, stderr = commands._run_process([sys.executable,str(Path(commands.__file__).resolve()),'--agent-worker'],
                cwd=str(tmp_path),timeout=5,input_text=json.dumps({'prompt':'test tool cancellation','command_timeout':1}))
            assert code == 1 and not stdout and ('timed out' in stderr or 'max_turns' in stderr)
        time.sleep(1.3)
        assert not marker.exists()
    finally:
        server.shutdown();server.server_close();thread.join(timeout=2)


def test_redaction_handles_unicode_json_and_raw(monkeypatch):
    secret = 'synthetic-雪-"quoted"-token'
    monkeypatch.setenv("SYNTHETIC_API_KEY", secret)
    variants = [secret, json.dumps(secret)[1:-1], json.dumps(secret, ensure_ascii=False)[1:-1]]
    for variant in variants:
        assert commands._redact(variant) == "[REDACTED]"


def test_deadline_kills_term_ignoring_descendant_after_leader_exits(monkeypatch, tmp_path):
    import time
    monkeypatch.setenv("WORKSPACE", str(tmp_path))
    marker = tmp_path / "term-ignoring-survivor"
    child = ("import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);"
             f"time.sleep(2);open({str(marker)!r},'w').write('bad')")
    leader = ("import subprocess,sys,time;subprocess.Popen([sys.executable,'-c'," + repr(child) +
              "],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(30)")
    with pytest.raises(RuntimeError, match="timed out"):
        commands._run_process([sys.executable,"-c",leader], cwd=str(tmp_path), timeout=1)
    time.sleep(1.3)
    assert not marker.exists()


def test_file_tool_limit_counts_bytes_and_rejects_oversized_writes(tmp_path):
    (tmp_path/"large.txt").write_text("雪"*50000)
    result = commands._tool("read_file", {"path":"large.txt"}, tmp_path, 10)
    assert len(result) < 45000
    with pytest.raises(ValueError, match="128 KiB"):
        commands._tool("write_file", {"path":"new.txt", "content":"雪"*50000}, tmp_path, 10)
    assert not (tmp_path/"new.txt").exists()


def test_public_worker_completes_actual_http_tool_round_trip(monkeypatch, tmp_path):
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    import threading
    monkeypatch.setenv('WORKSPACE', str(tmp_path))
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'synthetic-private-key')
    requests = []
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            request = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            requests.append(request)
            if len(requests) == 1:
                message = {'role':'assistant','content':None,'tool_calls':[{'id':'write-1','type':'function',
                    'function':{'name':'write_file','arguments':json.dumps({'path':'actual-artifact.txt','content':'completed'})}}]}
            else:
                assert request['messages'][-1] == {'role':'tool','tool_call_id':'write-1','content':'written'}
                message = {'role':'assistant','content':'done'}
            body = json.dumps({'choices':[{'message':message}]}).encode()
            self.send_response(200);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
        def log_message(self,*args):
            pass
    server = ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread = threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    monkeypatch.setenv('DEEPSEEK_BASE_URL',f'http://127.0.0.1:{server.server_port}')
    try:
        assert json.loads(commands.deepseek('write actual artifact',command_timeout=10)) == {'content':'done','tool_calls':1}
        assert (tmp_path/'actual-artifact.txt').read_text() == 'completed'
        assert len(requests) == 2
    finally:
        server.shutdown();server.server_close();thread.join(timeout=2)
