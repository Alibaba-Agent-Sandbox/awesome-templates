"""Real HTTP/Node suite results must be visible to strict acceptance counters."""
from __future__ import annotations

import importlib.util
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def test_complete_real_node_http_suite_has_countable_results(monkeypatch, capfd):
    spec = importlib.util.spec_from_file_location('node_web_real_http_runner', ROOT / 'scripts/run_local_e2e.py')
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    # This test uses existing Node/npm, no install/global state/HOME override.
    for name in list(os.environ):
        if any(part in name.upper() for part in ('KEY', 'TOKEN', 'SECRET', 'PASSWORD', 'CREDENTIAL')):
            monkeypatch.delenv(name, raising=False)
    original_home = os.environ.get('HOME')
    with tempfile.TemporaryDirectory(prefix='node-web-http-protocol-') as scratch:
        monkeypatch.setenv('TMPDIR', scratch)
        monkeypatch.setenv('npm_config_cache', str(Path(scratch) / 'npm-cache'))
        monkeypatch.setenv('npm_config_userconfig', os.devnull)
        monkeypatch.setenv('npm_config_update_notifier', 'false')
        status, detail = runner._run_one(HERE, str(Path(sys.executable).parent))
        stdout = capfd.readouterr().out
    assert os.environ.get('HOME') == original_home
    assert status == 'pass', detail
    # Same strict anchored protocol used by the actual-image acceptance owner.
    counts = {category: len(re.findall(r'^\[' + category + r'\]', stdout, re.M))
              for category in ('PASS', 'FAIL', 'SKIP')}
    assert counts == {'PASS': 60, 'FAIL': 0, 'SKIP': 0}, counts
    assert 'node-web: 60 passed; L0 only' in stdout


def test_unhealthy_real_http_response_is_a_countable_failure(tmp_path):
    # Deterministic HTTP failure fixture, separate from the real Node positive
    # suite. No model, fake CLI, file upload or subprocess service is selected.
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            payload = b'{"status":"unhealthy"}'
            self.send_response(503)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        def log_message(self, *args): pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        env = {name: os.environ[name] for name in ('PATH', 'HOME', 'LANG', 'LC_ALL') if name in os.environ}
        env.update(E2E_BASE_URL=f'http://127.0.0.1:{server.server_port}', E2E_WORKSPACE=str(tmp_path))
        result = subprocess.run([sys.executable, str(HERE / 'e2e_test.py')], env=env,
                                capture_output=True, text=True, timeout=15)
        assert result.returncode != 0
        assert len(re.findall(r'^\[FAIL\]', result.stdout, re.M)) == 1
        assert not re.findall(r'^\[PASS\]', result.stdout, re.M)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        assert not thread.is_alive()
