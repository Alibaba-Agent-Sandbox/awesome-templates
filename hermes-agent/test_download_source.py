"""Real HTTP retry/integrity failures never become extracted source artifacts."""
from contextlib import contextmanager
import hashlib
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import importlib.util
from pathlib import Path
import threading
import pytest

spec=importlib.util.spec_from_file_location('hermes_pinned_fetch',Path(__file__).with_name('download_source.py'))
fetcher=importlib.util.module_from_spec(spec);spec.loader.exec_module(fetcher)
PAYLOAD=b'actual source fixture bytes\n'


@contextmanager
def server(statuses):
    calls=[]
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            code=statuses[min(len(calls),len(statuses)-1)];calls.append(code)
            self.send_response(code);self.send_header('Retry-After','0');self.end_headers()
            self.wfile.write(PAYLOAD)
        def log_message(self,*args):pass
    native=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=native.serve_forever,daemon=True);thread.start()
    try:yield 'http://127.0.0.1:'+str(native.server_port)+'/source.tar.gz',calls
    finally:native.shutdown();native.server_close();thread.join(timeout=3)


def test_rate_limit_then_verified_success_is_atomic(tmp_path):
    output=tmp_path/'source.tar.gz'
    with server([429,200])as(url,calls):
        fetcher.fetch(url,output,len(PAYLOAD),hashlib.sha256(PAYLOAD).hexdigest(),_test_http=True)
    assert calls==[429,200]and output.read_bytes()==PAYLOAD
    assert list(tmp_path.iterdir())==[output]


def test_retry_count_is_bounded_and_partial_file_is_removed(tmp_path):
    output=tmp_path/'source.tar.gz'
    with server([429])as(url,calls):
        with pytest.raises(RuntimeError,match='download failed'):
            fetcher.fetch(url,output,len(PAYLOAD),hashlib.sha256(PAYLOAD).hexdigest(),attempts=2,_test_http=True)
    assert calls==[429,429]and not output.exists()and list(tmp_path.iterdir())==[]


def test_integrity_failure_preserves_existing_destination(tmp_path):
    output=tmp_path/'source.tar.gz';output.write_bytes(b'caller-owned')
    with server([200])as(url,calls):
        with pytest.raises(ValueError,match='integrity'):
            fetcher.fetch(url,output,len(PAYLOAD),'0'*64,_test_http=True)
    assert calls==[200]and output.read_bytes()==b'caller-owned'and list(tmp_path.iterdir())==[output]


def test_non_transient_error_is_not_retried(tmp_path):
    with server([403])as(url,calls):
        with pytest.raises(RuntimeError,match='rejected'):
            fetcher.fetch(url,tmp_path/'source.tar.gz',len(PAYLOAD),hashlib.sha256(PAYLOAD).hexdigest(),_test_http=True)
    assert calls==[403]


def test_cleartext_requires_explicit_local_fixture_opt_in(tmp_path):
    with pytest.raises(ValueError,match='HTTPS'):
        fetcher.fetch('http://example.invalid/source',tmp_path/'source',1,'0'*64)


def test_cached_source_keeps_the_same_integrity_rule(tmp_path):
    source=tmp_path/'cached';source.write_bytes(PAYLOAD);output=tmp_path/'output'
    fetcher.cached(source,output,len(PAYLOAD),hashlib.sha256(PAYLOAD).hexdigest())
    assert output.read_bytes()==PAYLOAD
    source.write_bytes(b'corrupted')
    with pytest.raises(ValueError,match='integrity'):
        fetcher.cached(source,output,len(PAYLOAD),hashlib.sha256(PAYLOAD).hexdigest())
    assert output.read_bytes()==PAYLOAD
