"""Actual pinned Pi against a local protocol fixture; this is not model acceptance."""
import importlib.util
import json
from pathlib import Path
import shutil
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import pytest

SPEC=importlib.util.spec_from_file_location('pi_cli_protocol_commands',Path(__file__).with_name('commands.py'))
commands=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(commands)


@pytest.mark.skipif(shutil.which('pi') is None,reason='actual pinned Pi CLI is not installed')
@pytest.mark.parametrize('allow_tools',[False,True])
def test_actual_cli_exposes_only_selected_tools_and_ignores_project_extensions(monkeypatch,tmp_path,allow_tools):
    requests=[]
    authorization=[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            requests.append(body)
            authorization.append(self.headers.get("Authorization"))
            self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
            for chunk in [
                {'id':'fixture','object':'chat.completion.chunk','choices':[{'index':0,'delta':{'role':'assistant','content':'protocol-ok'},'finish_reason':None}]},
                {'id':'fixture','object':'chat.completion.chunk','choices':[{'index':0,'delta':{},'finish_reason':'stop'}]},
            ]:self.wfile.write(('data: '+json.dumps(chunk)+'\n\n').encode())
            self.wfile.write(b'data: [DONE]\n\n')
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        marker=tmp_path/'project-extension-executed'
        extension=tmp_path/'.pi/extensions/hostile.js';extension.parent.mkdir(parents=True)
        extension.write_text("import {writeFileSync} from 'node:fs';writeFileSync("+json.dumps(str(marker))+",'bad');export default function(){}")
        monkeypatch.setenv('WORKSPACE',str(tmp_path));monkeypatch.setenv('PI_BASE_URL',f'http://127.0.0.1:{server.server_port}/v1')
        monkeypatch.setenv('PI_MODEL','fixture-model');monkeypatch.setenv('PI_API_KEY','synthetic-protocol-key')
        assert commands.pi_version()=='1.3.0'
        output=commands.pi('Return protocol-ok',allow_tools=allow_tools,command_timeout=30)
        assert 'protocol-ok' in output and requests and not marker.exists()
        tools={tool['function']['name'] for tool in requests[0]['tools']}
        assert tools==({'read','grep','find','ls','edit','write','bash'} if allow_tools else {'read','grep','find','ls'})
        assert requests[0]['model']=='fixture-model'
        assert authorization == ['Bearer synthetic-protocol-key']
    finally:
        server.shutdown();server.server_close();thread.join(timeout=5)


@pytest.mark.skipif(shutil.which('pi') is None,reason='actual pinned Pi CLI is not installed')
def test_actual_offline_read_find_grep_ls_execute_without_a_model():
    assert commands.pi_tools_check()=='read/find/grep/ls OK'


@pytest.mark.skipif(shutil.which('pi') is None,reason='actual pinned Pi CLI is not installed')
@pytest.mark.parametrize('missing',['fd','rg'])
def test_actual_offline_tool_smoke_rejects_missing_runtime_binary(monkeypatch,tmp_path,missing):
    binaries={name:shutil.which(name) for name in ['node','pi','fd','rg']}
    assert all(binaries.values()),'install the official pinned tool dependencies for this test'
    for name,path in binaries.items():
        if name!=missing:(tmp_path/name).symlink_to(path)
    monkeypatch.setenv('PATH',str(tmp_path))
    with pytest.raises(RuntimeError,match=('fd is not available' if missing=='fd' else 'ripgrep.*not available')):
        commands.pi_tools_check()
