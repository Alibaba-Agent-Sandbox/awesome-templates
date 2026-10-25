"""Real subprocess regressions for full HTTP acceptance and fixture isolation."""
import json

import pytest

from template_http_acceptance import controller_environment, fixture_environment, run_controller


def controller(tmp_path, name, text):
    source = tmp_path / name
    source.mkdir()
    (source / "e2e_test.py").write_text(text)
    return source


def test_operator_credentials_cannot_reach_actual_controller(tmp_path, monkeypatch):
    for key in ["OPENAI_API_KEY", "ABX_SANDBOX_API_KEY", "CURSOR_API_KEY", "GH_TOKEN"]:
        monkeypatch.setenv(key, "synthetic-operator-secret")
    source = controller(tmp_path, "example", "import os\nassert not any(k in os.environ for k in ['OPENAI_API_KEY','ABX_SANDBOX_API_KEY','CURSOR_API_KEY','GH_TOKEN'])\nassert os.environ['E2E_RUN_LLM']=='0'\nprint('[PASS] credentials isolated')\n")
    proof = run_controller(source, {9000: "http://synthetic.invalid"}, tmp_path, {})
    assert proof["passed"] and proof["pass_count"] == 1


@pytest.mark.parametrize("name,output", [
    ("openclaw", "[PASS] health\n[SKIP] real gateway lifecycle"),
    ("osworld", "[PASS] version\n[SKIP] desktop"),
    ("cursor-agent", "[PASS] version\n[SKIP] authentication"),
    ("devin", "[PASS] version\n[SKIP] authentication"),
    ("chrome", "[PASS] version\n[SKIP] desktop"),
    ("example", ""),
    ("example", "[PASS] health\n[FAIL] actual operation"),
])
def test_zero_exit_does_not_hide_missing_or_failed_operations(tmp_path, name, output):
    source = controller(tmp_path, name, "print(" + repr(output) + ")\n")
    _, fixture, _ = fixture_environment(name)
    urls = {port: "http://synthetic.invalid" for port in [9000, 9222, 6080]}
    assert run_controller(source, urls, tmp_path, fixture)["passed"] is False


def test_gateway_token_is_shared_only_with_owned_servers_and_not_evidence():
    server, controller_env, proof = fixture_environment("openclaw")
    token = server["OPENCLAW_GATEWAY_TOKEN"]
    assert controller_env["OPENCLAW_GATEWAY_TOKEN"] == token
    assert len(token) >= 40 and token not in json.dumps(proof)
    assert proof["gateway_lifecycle_required"]


def test_unrelated_secret_cannot_be_forwarded_as_a_fixture(tmp_path):
    with pytest.raises(ValueError, match="only owned"):
        controller_environment(tmp_path, {9000: "http://synthetic.invalid"},
                               {"OPENAI_API_KEY": "synthetic-secret"})


def test_actual_https_controller_retains_verification_with_configured_ca(tmp_path, monkeypatch):
    import http.server
    import socketserver
    import ssl
    import subprocess
    import threading
    cert, key = tmp_path / 'fixture-cert.pem', tmp_path / 'fixture-key.pem'
    subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes',
        '-keyout', str(key), '-out', str(cert), '-days', '1', '-subj', '/CN=localhost',
        '-addext', 'subjectAltName=DNS:localhost,IP:127.0.0.1'],
        check=True, capture_output=True)
    key.chmod(0o600)

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-Length', str(len(b'owned TLS health')))
            self.end_headers()
            self.wfile.write(b'owned TLS health')

        def log_message(self, *args):
            pass

    # A Unix socket keeps this real TLS fixture independent of transparent
    # network proxies that replace certificates on loopback TCP connections.
    socket_path = tmp_path / 'tls.sock'
    server = socketserver.UnixStreamServer(str(socket_path), Handler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert, key)
    server.socket = context.wrap_socket(server.socket, server_side=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        monkeypatch.setenv('SSL_CERT_FILE', str(cert))
        source = controller(tmp_path, 'tls-example', "import os,httpx\ntransport=httpx.HTTPTransport(uds=" + repr(str(socket_path)) + ")\nwith httpx.Client(transport=transport) as client:\n r=client.get(os.environ['E2E_BASE_URL']+'/health');assert r.status_code==200 and r.content==b'owned TLS health'\nprint('[PASS] verified actual HTTPS health')\n")
        proof = run_controller(source, {9000: 'https://localhost'}, tmp_path, {})
        assert proof['passed'] and proof['pass_count'] == 1
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_application_token_is_explicit_and_not_borrowed_from_operator(tmp_path, monkeypatch):
    monkeypatch.setenv('E2E_TOKEN', 'unrelated-operator-token')
    monkeypatch.setenv('ABX_SERVER_TOKEN', 'unrelated-server-token')
    source = controller(tmp_path, 'example', "import os\nassert os.environ['E2E_TOKEN']=='owned-application-token'\nassert os.environ['ABX_SERVER_TOKEN']=='owned-application-token'\nprint('[PASS] explicit owned application token')\n")
    environment = controller_environment(source, {9000: 'http://synthetic.invalid'}, {})
    assert 'E2E_TOKEN' not in environment
    proof = run_controller(source, {9000: 'http://synthetic.invalid'}, tmp_path, {}, token='owned-application-token')
    assert proof['passed'] and proof['pass_count'] == 1
