"""Exercise actual ranged HTTP, integrity failures and process-local caching."""
from contextlib import contextmanager
import ast
import base64
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import platform
import shutil
import shlex
import subprocess
import sys
import threading
import zlib

import pytest

import step_assets
from prepare_steps import ROOT, prepare


@contextmanager
def server(content, *, malformed=False):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            start, end = map(int, self.headers["Range"].removeprefix("bytes=").split("-"))
            self.send_response(206)
            self.send_header("Content-Range", "invalid" if malformed else f"bytes {start}-{end}/{len(content)}")
            self.end_headers()
            self.wfile.write(content[start:end + 1])

        def log_message(self, *args):
            pass

    http = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=http.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{http.server_port}/archive"
    finally:
        http.shutdown()
        http.server_close()
        thread.join()


def test_actual_ranges_reconstruct_exact_bytes(tmp_path):
    content = bytes(range(256)) * 4097
    target = tmp_path / "archive"
    with server(content) as url:
        step_assets.download({"url": url, "sha256": hashlib.sha256(content).hexdigest(), "size": len(content)}, target, workers=3)
    assert target.read_bytes() == content


def test_tau2_original_archive_recipe_fits_wire_and_preserves_source():
    manifest, proof = prepare(ROOT / "tau2-bench", asset_transport="parallel",
                              server_commit="e2cb27e24fde0a67112f82b8d44af463445a5d1a")
    assert proof["steps_json_bytes"] <= 15000
    assert len(proof["copy_source_commit"]) == 40
    original = ROOT / "tau2-bench" / "install_source.py"
    assert proof["inputs_sha256"]["install_source.py"] == hashlib.sha256(original.read_bytes()).hexdigest()
    assets = proof["build_assets"]["x86_64"]
    assert assets == [{"url": "https://codeload.github.com/sierra-research/tau2-bench/tar.gz/fc0055dc4e0a316c3f83133267fbd6faaa770992",
                       "size": 92081935, "sha256": "7a227036d07fdeb088dbd0c99fdb40ee9b9e0ebc06aadbc4dec1217b3383e57e"}]
    assert manifest["build"]["steps"][-1] == {"type": "USER", "args": ["user"]}
    assert "/tmp/abx-step-assets" in manifest["build"]["steps"][-2]["args"][0]


@pytest.mark.parametrize("field,value", [("url", "https://unreviewed.invalid/source"),
                                         ("sha256", "0" * 64), ("size", 1)])
def test_tau2_transport_refuses_changed_upstream_metadata(tmp_path, field, value):
    from prepare_steps import parallel_assets
    source = tmp_path / "tau2-bench"
    source.mkdir()
    item = json.loads((ROOT / "tau2-bench" / "upstream.json").read_text())
    item[field] = value
    (source / "upstream.json").write_text(json.dumps(item))
    with pytest.raises(ValueError, match="unreviewed Tau2 source transport"):
        parallel_assets(source)


@pytest.mark.parametrize("failure", ["range", "size", "digest"])
def test_invalid_archive_cannot_be_published(tmp_path, failure):
    content = b"archive" * 100
    target = tmp_path / "archive"
    with server(content, malformed=failure == "range") as url:
        asset = {"url": url, "sha256": "0" * 64 if failure == "digest" else hashlib.sha256(content).hexdigest(),
                 "size": len(content) + (1 if failure == "size" else 0)}
        with pytest.raises(RuntimeError):
            step_assets.download(asset, target)
    assert not target.exists()
    assert not list(tmp_path.glob("parts-*"))


@pytest.mark.parametrize("method", ["urlopen", "urlretrieve"])
def test_installer_consumes_only_exact_verified_cache(tmp_path, method):
    content = b"immutable-official-archive"
    digest = hashlib.sha256(content).hexdigest()
    (tmp_path / digest).write_bytes(content)
    (tmp_path / "assets.json").write_text(json.dumps({platform.machine(): [{"url": "https://official.invalid/archive", "sha256": digest}]}))
    helper = tmp_path / "step_assets.py"
    shutil.copy2(Path(step_assets.__file__), helper)
    script = tmp_path / "installer.py"
    script.write_text("import urllib.request\n" + (
        "with urllib.request.urlopen('https://official.invalid/archive') as f: print(f.read().decode())\n" if method == "urlopen" else
        "from pathlib import Path\npath,_=urllib.request.urlretrieve('https://official.invalid/archive');print(Path(path).read_text())\n"))
    command = [sys.executable, str(helper), "run", str(script)]
    assert subprocess.check_output(command, text=True).strip() == content.decode()
    (tmp_path / digest).write_bytes(b"tampered")
    result = subprocess.run(command, text=True, capture_output=True)
    assert result.returncode != 0 and "cache integrity mismatch" in result.stderr
    assert script.read_text().startswith("import urllib.request")


def test_osworld_private_transport_keeps_hashes_on_regional_package_mirror():
    from prepare_steps import parallel_assets
    import platform
    assets = parallel_assets(ROOT / "osworld")[platform.machine()]
    manifest, _ = prepare(ROOT / "osworld", asset_transport="oss", asset_cache={
        "architecture": platform.machine(),
        "urls": {item["url"]: "https://private.invalid/object" for item in assets},
    })
    command = next(s["args"][0] for s in manifest["build"]["steps"]
                   if s["type"] == "RUN" and "--require-hashes" in s["args"][0])
    assert "--no-build-isolation --require-hashes -r /opt/osworld/requirements.txt" in command
    assert "--default-index https://mirrors.aliyun.com/pypi/simple/" in command


@pytest.mark.parametrize("name", ["goose", "crush", "code-server", "polyglot-toolchain", "aider", "swe", "hermes-agent", "openclaw"])
def test_generated_cache_preserves_original_source_and_is_removed_before_runtime(name):
    manifest, proof = prepare(ROOT / name, asset_transport="parallel", server_commit="e2cb27e24fde0a67112f82b8d44af463445a5d1a")
    steps = manifest["build"]["steps"]
    assert proof["asset_transport"] == "parallel"
    assert proof["steps_json_bytes"] <= 15000
    assert any("step_assets.py fetch 0" in step["args"][0] for step in steps if step["type"] == "RUN")
    if name not in {"hermes-agent", "aider"}:
        commands = []
        for step in steps:
            if step["type"] != "RUN":
                continue
            command = step["args"][0]
            if command.startswith("python3 -c ") and "os.execv(" in command:
                tree = ast.parse(shlex.split(command)[2])
                data = next(node.args[0].value for node in ast.walk(tree)
                            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "b64decode")
                command = zlib.decompress(base64.b64decode(data)).decode()
            commands.append(command)
        assert any("step_assets.py run" in command for command in commands)
    if name == "hermes-agent":
        assert proof["python_download_profile"].startswith("uv0.12.3")
        assert any("uv python install cpython-3.14.6-linux-$(uname -m)-gnu" in step["args"][0] for step in steps if step["type"] == "RUN")
        assert any("tar -xz --strip-components=1 -C /opt/hermes -f /tmp/abx-step-assets/" in step["args"][0] for step in steps if step["type"] == "RUN")
        assert not any("curl -fsSL https://codeload.github.com/NousResearch/hermes-agent/" in step["args"][0] for step in steps if step["type"] == "RUN")
    assert steps[-1] == {"type": "USER", "args": ["user"]}
    # compact_run retains short cleanup commands in plaintext.
    assert "rm -rf /tmp/abx-step-assets" in steps[-2]["args"][0]


@pytest.mark.parametrize("name", ["deepagents", "osworld", "browser-use"])
def test_parallel_locked_installer_retains_hashes_and_removes_build_tool(name):
    manifest, proof = prepare(ROOT / name, asset_transport="parallel", server_commit="e2cb27e24fde0a67112f82b8d44af463445a5d1a")
    commands = [step["args"][0] for step in manifest["build"]["steps"] if step["type"] == "RUN"]
    locked = [command for command in commands if "uv --no-cache pip install" in command and "--require-hashes" in command]
    assert len(locked) == 1 and "--require-hashes" in locked[0]
    assert "uv0.12.3" in proof["python_package_transport"]
    assert manifest["build"]["steps"][-2]["args"][0].startswith("rm -rf ")
    assert "/tmp/abx-step-installer" in manifest["build"]["steps"][-2]["args"][0]
    assert proof["steps_json_bytes"] <= 15000
    if name == "browser-use":
        assert any("step_assets.py playwright python3 -m playwright install chromium --no-shell" in command for command in commands)
        assert any("assert sys.version_info[:2] == (3,13)" in command for command in commands)
        assert any("rootfs exceeds8GiB" in command for command in commands)
        assert all("headless-shell" not in item["url"] for item in proof["build_assets"]["x86_64"])


@pytest.mark.parametrize("requested,exit_code", [("/fixed/browser.zip", 0), ("/assets.json", 1)])
def test_loopback_browser_mirror_serves_only_verified_archives(tmp_path, requested, exit_code):
    content = b"fixed official browser zip fixture"
    digest = hashlib.sha256(content).hexdigest()
    (tmp_path / digest).write_bytes(content)
    (tmp_path / "assets.json").write_text(json.dumps({platform.machine(): [
        {"url": "https://official.invalid/browser.zip", "sha256": digest, "playwright_path": "fixed/browser.zip"}]}))
    helper = tmp_path / "step_assets.py"
    shutil.copy2(Path(step_assets.__file__), helper)
    program = ("import os,urllib.request; "
               f"print(urllib.request.urlopen(os.environ['PLAYWRIGHT_DOWNLOAD_HOST']+{requested!r}).read().decode())")
    result = subprocess.run([sys.executable, str(helper), "playwright", sys.executable, "-c", program],
                            capture_output=True, text=True, timeout=15)
    assert result.returncode == exit_code
    if exit_code == 0:
        assert result.stdout.strip() == content.decode()


def test_stagehand_native_browser_recipe_fits_wire_and_uses_exact_immutable_copy():
    manifest, proof = prepare(ROOT / 'stagehand', asset_transport='parallel', server_commit='e2cb27e24fde0a67112f82b8d44af463445a5d1a')
    assert proof['steps_json_bytes'] <= 15000
    assert proof['copy_source_commit'] and len(proof['copy_source_commit']) == 40
    assert proof['inputs_sha256']['commands.py'] == hashlib.sha256((ROOT/'stagehand/commands.py').read_bytes()).hexdigest()
    assets = proof['build_assets']['x86_64']
    assert any('145.0.7632.6/linux64/chrome-linux64.zip' in x['url'] and x['size']==175440843 for x in assets)
    assert all('headless-shell' not in x['url'] for x in assets)
    commands = [s['args'][0] for s in manifest['build']['steps'] if s['type']=='RUN']
    assert any('step_assets.py playwright python3 -m playwright install chromium --no-shell' in x for x in commands)
    assert manifest['build']['steps'][-1] == {'type':'USER','args':['user']}
    assert '/tmp/abx-step-installer' in manifest['build']['steps'][-2]['args'][0]


def test_appworld_original_data_profile_rejects_unreviewed_identity(tmp_path):
    from prepare_steps import parallel_assets
    source=tmp_path/'appworld';source.mkdir()
    item=json.loads((ROOT/'appworld/upstream.json').read_text())
    (source/'upstream.json').write_text(json.dumps(item))
    assert parallel_assets(source)=={'x86_64':[{key:item['data'][key] for key in ['url','size','sha256']}]}
    for key,value in [('url','https://s3.us-west-2.amazonaws.com/other/data.bundle'),('size',1),('sha256','0'*64)]:
        changed=json.loads(json.dumps(item));changed['data'][key]=value
        (source/'upstream.json').write_text(json.dumps(changed))
        with pytest.raises(ValueError,match='unreviewed original encrypted AppWorld'):
            parallel_assets(source)


def test_appworld_encrypted_data_steps_preserve_exact_source_and_wire_limit():
    manifest,proof=prepare(ROOT/'appworld',asset_transport='parallel',server_commit='e2cb27e24fde0a67112f82b8d44af463445a5d1a')
    assert proof['steps_json_bytes']<=15000 and len(proof['copy_source_commit'])==40
    assert proof['inputs_sha256']['worker.py']==hashlib.sha256((ROOT/'appworld/worker.py').read_bytes()).hexdigest()
    assert proof['build_assets']['x86_64'][0]['size']==34280074
    assert manifest['build']['steps'][-1]=={'type':'USER','args':['user']}


def test_chrome_asset_profile_rejects_changed_official_identity(tmp_path):
    from prepare_steps import parallel_assets
    source=tmp_path/'chrome';source.mkdir()
    data=json.loads((ROOT/'chrome/browser.json').read_text())
    (source/'browser.json').write_text(json.dumps(data))
    assert parallel_assets(source)=={'x86_64':[{key:data[key]for key in ['url','size','sha256']}]}
    for key,value in [('browser_version','145.0.0.0'),('url','https://other.invalid/browser.zip'),('size',1),('sha256','0'*64)]:
        changed=dict(data);changed[key]=value
        (source/'browser.json').write_text(json.dumps(changed))
        with pytest.raises(ValueError,match='unreviewed headed Chrome'):parallel_assets(source)


def test_chrome_steps_preserve_native_archive_and_immutable_wire_budget():
    manifest,proof=prepare(ROOT/'chrome',asset_transport='parallel',server_commit='e2cb27e24fde0a67112f82b8d44af463445a5d1a')
    assert proof['steps_json_bytes']<=15000
    assert len(proof['copy_source_commit'])==40
    assert proof['inputs_sha256']['worker.py']==hashlib.sha256((ROOT/'chrome/worker.py').read_bytes()).hexdigest()
    assert len(proof['build_assets']['x86_64'])==1
    assert proof['build_assets']['x86_64'][0]['size']==175440843
    assert manifest['build']['steps'][-1]=={'type':'USER','args':['user']}
    assert 'rm -rf /tmp/abx-step-assets' in manifest['build']['steps'][-2]['args'][0]


def test_prime_asset_profile_rejects_changed_official_identity(tmp_path):
    from prepare_steps import parallel_assets
    source=tmp_path/'prime-agent';source.mkdir()
    data=json.loads((ROOT/'prime-agent/upstream.json').read_text())
    (source/'upstream.json').write_text(json.dumps(data))
    assert parallel_assets(source)=={'x86_64':[{key:data[key]for key in ['url','size','sha256']}]}
    for key,value in [('version','0.0.0'),('source_commit','0'*40),('url','https://other.invalid/native.tar.gz'),('size',1),('sha256','0'*64),('binary_size',1),('binary_sha256','0'*64)]:
        changed=dict(data);changed[key]=value
        (source/'upstream.json').write_text(json.dumps(changed))
        with pytest.raises(ValueError,match='unreviewed original Prime Agent'):parallel_assets(source)


def test_prime_steps_preserve_original_kernel_and_immutable_wire_budget():
    manifest,proof=prepare(ROOT/'prime-agent',asset_transport='parallel',server_commit='e2cb27e24fde0a67112f82b8d44af463445a5d1a')
    assert proof['steps_json_bytes']<=15000
    assert len(proof['copy_source_commit'])==40
    assert proof['inputs_sha256']['kernel-python']==hashlib.sha256((ROOT/'prime-agent/kernel-python').read_bytes()).hexdigest()
    assert set(proof['build_assets'])=={'x86_64'}
    assert proof['build_assets']['x86_64'][0]['size']==21556959
    assert manifest['build']['steps'][-1]=={'type':'USER','args':['user']}


@pytest.mark.parametrize('name',['qm','qm-sandbox'])
def test_qm_exact_source_profile_rejects_unreviewed_assets(tmp_path,name):
    from prepare_steps import parallel_assets
    source=tmp_path/name;source.mkdir()
    original=json.loads((ROOT/name/'upstream.json').read_text())
    (source/'upstream.json').write_text(json.dumps(original))
    assert len(parallel_assets(source)['x86_64'])==3
    for asset in ['node','qm','agent-sandbox-node-sdk']:
        for key,value in [('url','https://other.invalid/source.tar.gz'),('size',1),('sha256','0'*64)]:
            changed=json.loads(json.dumps(original));changed[asset][key]=value
            (source/'upstream.json').write_text(json.dumps(changed))
            with pytest.raises(ValueError,match='unreviewed original QM/SDK/Node'):parallel_assets(source)


@pytest.mark.parametrize('name',['qm','qm-sandbox'])
def test_qm_native_steps_keep_exact_original_inputs_and_wire_budget(name):
    from server_sdk_pin import server_commit
    selected=server_commit(ROOT/name)
    manifest,proof=prepare(ROOT/name,asset_transport='parallel',server_commit=selected)
    assert proof['template_server_commit']==selected and selected=='34e7e011c5569f77b7f605e65313be7498f6cf02'
    assert proof['steps_json_bytes']<=15000 and len(proof['copy_source_commit'])==40
    for filename in ['worker.mjs','adapter.mjs','tool_process.py','sdk_exec.py']:
        assert proof['inputs_sha256'][filename]==hashlib.sha256((ROOT/name/filename).read_bytes()).hexdigest()
    assert len(proof['build_assets']['x86_64'])==3
    assert manifest['build']['steps'][-1]=={'type':'USER','args':['user']}
