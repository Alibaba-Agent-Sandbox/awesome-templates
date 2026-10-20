"""A delayed real Node startup must not make a missing entry look successful."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import shutil
import shlex
import signal
import subprocess

import pytest


def test_missing_entry_rejected_before_delayed_node_startup(tmp_path, monkeypatch):
    node = shutil.which('node')
    assert node, 'This regression requires a real Node runtime'
    shim = tmp_path / 'bin'
    shim.mkdir()
    script = shim / 'node'
    script.write_text('#!/bin/sh\nsleep 3\nexec ' + shlex.quote(node) + ' "$@"\n')
    script.chmod(0o755)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('WORKSPACE', str(tmp_path))
    monkeypatch.setenv('PATH', str(shim) + os.pathsep + os.environ['PATH'])
    spec = importlib.util.spec_from_file_location('node_web_startup_regression', Path(__file__).with_name('commands.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    processes = []
    real_popen = subprocess.Popen

    def owned_popen(*args, **kwargs):
        process = real_popen(*args, **{**kwargs, 'start_new_session': True})
        processes.append(process)
        return process

    monkeypatch.setattr(subprocess, 'Popen', owned_popen)
    try:
        with pytest.raises((RuntimeError, ValueError), match='entry'):
            module.serve(entry='missing-entry.js', port=3999)
    finally:
        for process in processes:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.communicate(timeout=5)


def test_closed_http_connection_time_wait_does_not_block_real_node_rebind(tmp_path,monkeypatch):
    import http.client
    import http.server
    import threading
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200);self.send_header('Connection','close');self.end_headers();self.wfile.write(b'old-owned-response')
        def log_message(self,*args):pass
    previous=http.server.HTTPServer(('0.0.0.0',0),Handler);port=previous.server_port
    thread=threading.Thread(target=previous.serve_forever,daemon=True);thread.start()
    connection=http.client.HTTPConnection('127.0.0.1',port,timeout=5)
    try:
        connection.request('GET','/');assert connection.getresponse().read()==b'old-owned-response'
    finally:
        connection.close();previous.shutdown();previous.server_close();thread.join(timeout=2)
    monkeypatch.setenv('WORKSPACE',str(tmp_path))
    app=tmp_path/'index.js';app.write_text("require('http').createServer((q,r)=>r.end('new-real-node')).listen(Number(process.env.PORT),'0.0.0.0')")
    spec=importlib.util.spec_from_file_location('node_web_time_wait_regression',Path(__file__).with_name('commands.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    try:
        assert module.serve(entry='index.js',port=port,timeout_s=10)['status']=='running'
        assert module.request()['body']=='new-real-node'
    finally:module.stop()


def test_active_unrelated_listener_remains_rejected(tmp_path,monkeypatch):
    import socket
    monkeypatch.setenv('WORKSPACE',str(tmp_path));(tmp_path/'index.js').write_text('setTimeout(()=>{},10000)')
    spec=importlib.util.spec_from_file_location('node_web_unrelated_listener_regression',Path(__file__).with_name('commands.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    with socket.socket() as listener:
        listener.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);listener.bind(('0.0.0.0',0));listener.listen()
        with pytest.raises(RuntimeError,match='already in use'):module.serve(entry='index.js',port=listener.getsockname()[1])
        assert listener.fileno()>=0
