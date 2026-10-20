"""Actual pinned native SDK against an authored CDP transport, no browser/model."""
import base64
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
from pathlib import Path
import secrets
import shutil
import struct
import subprocess
import threading
import pytest

s=importlib.util.spec_from_file_location('stagehand_exact_sdk_patch',Path(__file__).with_name('patch_sdk.py'))
p=importlib.util.module_from_spec(s)
s.loader.exec_module(p)


@pytest.mark.parametrize('patched,explicit,expected',[
    (False,True,'Extensions.getExtensions'),
    (True,True,'Target.getTargets'),
    (True,False,'Extensions.getExtensions'),
])
def test_real_native_factory_forwards_extension_id_without_unsafe_install(patched,explicit,expected):
    native=Path(__file__).with_name('node_modules')/'@browserbasehq/stagehand/dist/index.mjs'
    if not native.is_file():pytest.fail('run the pinned npm ci before the actual SDK regression')
    candidate=native.with_name('owned-connect-regression-'+secrets.token_hex(8)+'.mjs')
    data=native.read_bytes();candidate.write_bytes(p.patched(data) if patched else data)
    methods=[]
    class Handler(BaseHTTPRequestHandler):
        protocol_version='HTTP/1.1'
        def log_message(self,*_):pass
        def do_GET(self):
            self.connection.settimeout(5)
            if self.path=='/json/version':
                body=json.dumps({'webSocketDebuggerUrl':'ws://127.0.0.1:'+str(self.server.server_port)+'/ws'}).encode()
                self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body);return
            key=self.headers['Sec-WebSocket-Key']
            accept=base64.b64encode(hashlib.sha1((key+'258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode()).digest()).decode()
            self.send_response(101);self.send_header('Upgrade','websocket');self.send_header('Connection','Upgrade');self.send_header('Sec-WebSocket-Accept',accept);self.end_headers();self.wfile.flush()
            first=self.rfile.read(2);assert len(first)==2
            length=first[1]&127
            if length==126:length=struct.unpack('!H',self.rfile.read(2))[0]
            if length==127:length=struct.unpack('!Q',self.rfile.read(8))[0]
            assert length<16384 and first[1]&128
            mask=self.rfile.read(4);value=self.rfile.read(length);value=bytes(v^mask[i%4] for i,v in enumerate(value));methods.append(json.loads(value)['method'])
            # Terminate after observing the first real SDK command; no browser is simulated as a pass.
            self.wfile.write(b'\x88\x00');self.wfile.flush();self.close_connection=True
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        options={'cdpUrl':'http://127.0.0.1:'+str(server.server_port)}
        if explicit:options['extensionId']='a'*32
        script='import {localBrowser} from '+json.dumps(candidate.as_uri())+';try{await localBrowser.connect('+json.dumps(options)+');process.exitCode=1;}catch{console.log("AUTHORED_CDP_CLOSED");}'
        result=subprocess.run([shutil.which('node'),'--input-type=module','-e',script],capture_output=True,text=True,timeout=15)
        assert result.returncode==0 and result.stdout.strip()=='AUTHORED_CDP_CLOSED'
        assert methods==[expected]
    finally:
        server.shutdown();server.server_close();thread.join(timeout=5);candidate.unlink(missing_ok=True)


def test_changed_upstream_bytes_cannot_receive_a_silent_compatibility_patch():
    with pytest.raises(ValueError,match='unreviewed'):p.patched(b'unreviewed native source')
