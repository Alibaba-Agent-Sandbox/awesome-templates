#!/usr/bin/env python3
"""Materialize this catalog's Dockerfile profile as explicit platform steps.

No Docker execution, cloud calls or directory upload occurs here. Only explicit
COPY inputs are embedded. Unsupported Docker instructions fail closed.
"""
from __future__ import annotations

import argparse
import ast
import base64
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
from string import Template
import zlib

import yaml

try:
    from .manifest_contract import manifest_contract_sha256
except ImportError:
    from manifest_contract import manifest_contract_sha256
try:
    from .server_sdk_pin import server_commit as pinned_server_commit
except ImportError:
    from server_sdk_pin import server_commit as pinned_server_commit

ROOT = Path(__file__).resolve().parents[1]
MATERIALIZER_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
BASE = "fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>"
BASE_PATH = "/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/.fce2b"


def parallel_assets(source: Path) -> dict:
    """Only reviewed installers with explicit public archive hashes opt in."""
    if source.name == "openclaw":
        for kind, command in instructions((source / "Dockerfile").read_text()):
            if kind != "RUN" or "architectures = {" not in command:
                continue
            code = command.split("\n", 1)[1].rsplit("\n", 1)[0]
            tree = ast.parse(code)
            mapping = next(ast.literal_eval(node.value) for node in tree.body
                           if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "architectures" for t in node.targets))
            version = re.search(r'name = f"node-v([0-9.]+)-linux-\{arch\}"', code)
            if not version:
                raise ValueError("unreviewed OpenClaw Node archive installer")
            pin = version[1]
            return {arch: [{"url": f"https://nodejs.org/dist/v{pin}/node-v{pin}-linux-{item[0]}.tar.gz", "sha256": item[1]}]
                    for arch, item in mapping.items()}
        raise ValueError("missing pinned OpenClaw Node archive")
    if source.name in {"goose", "crush"}:
        metadata = json.loads((source / "assets.json").read_text())["assets"]
        return {arch: [entry] for arch, entry in metadata.items()}
    if source.name == "code-server":
        entries = json.loads((source / "assets.json").read_text())["assets"]
        return {arch: [{"url": entry["browser_download_url"], "size": entry["size"],
                        "sha256": entry["digest"].removeprefix("sha256:")}]
                for arch, suffix in [("x86_64", "amd64"), ("aarch64", "arm64")]
                for entry in entries if entry["name"].endswith("-" + suffix + ".tar.gz")}
    if source.name == "polyglot-toolchain":
        metadata = json.loads((source / "toolchains.json").read_text())
        return {arch: [metadata["go"]["assets"][go], metadata["java"]["assets"][java],
                       *metadata["rust_components"][arch].values()]
                for arch, go, java in [("x86_64", "amd64", "x64"), ("aarch64", "arm64", "aarch64")]}
    if source.name in {"aider", "swe"}:
        for kind, command in instructions((source / "Dockerfile").read_text()):
            if kind != "RUN" or "checksums = {" not in command:
                continue
            code = command.split("\n", 1)[1].rsplit("\n", 1)[0]
            tree = ast.parse(code)
            checksums = next(ast.literal_eval(node.value) for node in tree.body
                             if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "checksums" for t in node.targets))
            pattern = re.search(r'name = f"(cpython-[0-9.+]+-\{arch\}-unknown-linux-gnu-install_only_stripped\.tar\.gz)"', code)
            if not pattern:
                raise ValueError("unreviewed standalone Python archive profile")
            release = re.search(r'python-build-standalone/releases/download/([0-9]{8})/', code)
            if not release:
                raise ValueError("standalone Python requires an immutable release")
            result = {arch: [{"url": "https://github.com/astral-sh/python-build-standalone/releases/download/" + release[1] + "/" + pattern[1].format(arch=arch),
                              "sha256": digest}] for arch, digest in checksums.items()}
            if source.name == "swe":
                wheels = json.loads(Path(__file__).with_name("step_uv_bootstrap.json").read_text())["assets"]
                for arch in result:
                    result[arch].append(wheels[arch])
            return result
        raise ValueError("unreviewed standalone Python installer")
    if source.name == "appworld":
        item = json.loads((source / "upstream.json").read_text())
        data = item["data"]
        if (item["version"] != "0.1.3.post1" or item["source_commit"] != "66ad8099e12188ece0d3fe45e661dbc01880813b"
                or data["url"] != "https://s3.us-west-2.amazonaws.com/appworld.dev/data-0.1.0.bundle"
                or data["size"] != 34280074 or data["sha256"] != "fd9f9608c2ec71ed0ac25c3633a738b9129a318a129e31230425b9188e508250"):
            raise ValueError("unreviewed original encrypted AppWorld data transport")
        return {"x86_64": [{key: data[key] for key in ["url", "size", "sha256"]}]}




    if source.name == 'devin':
        from step_assets import reviewed_devin_native
        metadata=json.loads((source/'upstream.json').read_text());item=metadata.get('archive',{})
        if metadata.get('version')!='3000.11.92'or metadata.get('architecture')!='x86_64'or not reviewed_devin_native(item):
            raise ValueError('unreviewed original Devin artifact transport')
        return {'x86_64':[{key:item[key]for key in ['url','size','sha256']}]}
    if source.name=='k3s':
        item=json.loads((source/'upstream.json').read_text())
        expected={'version':'v1.37.1+k3s1','architecture':'x86_64','url':'https://github.com/k3s-io/k3s/releases/download/v1.37.1%2Bk3s1/k3s','size':81543330,'sha256':'92b94582eb7b34a8cf532e6006842b9ed215a6783cf56a3dd6271fd35243b2c0'}
        if any(item.get(key)!=value for key,value in expected.items()):raise ValueError('unreviewed original K3s artifact transport')
        return {'x86_64':[{key:item[key]for key in ['url','size','sha256']}]}
    if source.name == "cursor-agent":
        from step_assets import reviewed_cursor_native
        metadata=json.loads((source/'upstream.json').read_text());item=metadata.get('archive',{})
        if metadata.get('version')!='2026.10.19-6bbf2c4'or metadata.get('architecture')!='x86_64'or not reviewed_cursor_native(item):
            raise ValueError('unreviewed original Cursor artifact transport')
        return {'x86_64':[{key:item[key]for key in ['url','size','sha256']}]}
    if source.name == "muse":
        from step_assets import reviewed_muse_native
        item = json.loads((source / "upstream.json").read_text())
        if item.get("version") != "1.4.11-R6667.1" or not reviewed_muse_native(item):
            raise ValueError("unreviewed original Muse native artifact transport")
        return {"x86_64": [{key: item[key] for key in ["url", "size", "sha256"]}]}
    if source.name in {"qm", "qm-sandbox"}:
        metadata = json.loads((source / "upstream.json").read_text())
        expected = {
            "node": ("https://nodejs.org/dist/v24.16.0/node-v24.16.0-linux-x64.tar.gz", 57023429, "2faf6a387e9b62b888e21c54f01249fb27537ffecf1842f29f4c919d0a59a0ff"),
            "qm": ("https://codeload.github.com/yc-software/qm/tar.gz/deef9b8b1e2b85bd4166dd833604bb31bcb8e255", 10625243, "40fb0d69319753a1cfab2dc8a1e8574d206e92589d26b264e768e94fa9109b4e"),
            "agent-sandbox-node-sdk": ("https://codeload.github.com/Alibaba-Agent-Sandbox/nodejs-sdk/tar.gz/90b5187dca84fca78d75d3045896482540641c72", 27746, "6b51e849090656de448812dbc5b08bb0a7ac0a981241739e116597cd8383cfd6"),
        }
        for name, identity in expected.items():
            item = metadata[name]
            if tuple(item[key] for key in ["url", "size", "sha256"]) != identity:
                raise ValueError("unreviewed original QM/SDK/Node archive transport")
        if (metadata["node"]["version"] != "24.16.0" or metadata["node"]["binary_size"] != 123438592
                or metadata["node"]["binary_sha256"] != "b2959781cc5a74c357ffa02367efa8a0330cbb1c9cb347732fdfaaaca381cbcd"
                or metadata["qm"]["source_commit"] != "deef9b8b1e2b85bd4166dd833604bb31bcb8e255"
                or metadata["agent-sandbox-node-sdk"]["source_commit"] != "90b5187dca84fca78d75d3045896482540641c72"):
            raise ValueError("unreviewed original QM/SDK/Node identity")
        return {"x86_64": [{key: metadata[name][key] for key in ["url", "size", "sha256"]} for name in expected]}
    if source.name == "prime-agent":
        item = json.loads((source / "upstream.json").read_text())
        if (item["version"] != "0.10.0"
                or item["source_commit"] != "763094e1b6a7c17450ee8399b06cda1853847ca5"
                or item["url"] != "https://github.com/PrimeIntellect-ai/prime-agent/releases/download/v0.10.0/prime-agent-0.10.0-linux-x64.tar.gz"
                or item["size"] != 21556959
                or item["sha256"] != "c16bd2af5e77b53f49b914a44742c4cf6a67c5ed5000041430b78dbd4c3bcbec"
                or item["binary_size"] != 61057216
                or item["binary_sha256"] != "546e71921bb0fa278c9d50dd8c61a27b835413552cb08a9359d0e320848e39d6"):
            raise ValueError("unreviewed original Prime Agent archive transport")
        return {"x86_64": [{key: item[key] for key in ["url", "size", "sha256"]}]}
    if source.name == "chrome":
        item = json.loads((source / "browser.json").read_text())
        if (item["browser_version"] != "145.0.7632.6"
                or item["url"] != "https://cdn.playwright.dev/chrome-for-testing-public/145.0.7632.6/linux64/chrome-linux64.zip"
                or item["size"] != 175440843
                or item["sha256"] != "b5e3195041af345a668d110f5daf5581961fa3608626ea588c97dd0fe81c4e38"):
            raise ValueError("unreviewed headed Chrome archive transport")
        return {"x86_64": [{key: item[key] for key in ["url", "size", "sha256"]}]}
    if source.name == "tau2-bench":
        item = json.loads((source / "upstream.json").read_text())
        if (item["source_commit"] != "fc0055dc4e0a316c3f83133267fbd6faaa770992" or item["url"] != "https://codeload.github.com/sierra-research/tau2-bench/tar.gz/" + item["source_commit"]
                or item["size"] != 92081935 or item["sha256"] != "7a227036d07fdeb088dbd0c99fdb40ee9b9e0ebc06aadbc4dec1217b3383e57e"):
            raise ValueError("unreviewed Tau2 source transport")
        return {arch: [{key: item[key] for key in ["url", "size", "sha256"]}]
                for arch in ["x86_64", "aarch64"]}
    if source.name == "hermes-agent":
        text = (source / "Dockerfile").read_text()
        metadata = json.loads(Path(__file__).with_name("step_uv_python.json").read_text())
        if "uv==" + metadata["uv_version"] not in text or "uv python install " + metadata["python_version"] not in text:
            raise ValueError("uv standalone-Python transport metadata must match the exact source pins")
        wheels = json.loads(Path(__file__).with_name("step_uv_bootstrap.json").read_text())["assets"]
        upstream = {
            "url": "https://codeload.github.com/NousResearch/hermes-agent/tar.gz/297552a9d646119871391d202509822cd86330df",
            "sha256": "fbd55e510b49592635429aa451a7c2b9fb4061cddbbab09f52504226f4338fcf",
            "size": 83225459,
            "digest_basis": "controller measured immutable upstream commit archive; not an upstream-published SHA256",
        }
        return {arch: [item, wheels[arch], upstream] for arch, item in metadata["assets"].items()}
    if source.name in {"deepagents", "osworld", "browser-use", "stagehand"}:
        metadata = json.loads(Path(__file__).with_name("step_uv_bootstrap.json").read_text())
        if source.name == "deepagents":
            return {arch: [item] for arch, item in metadata["assets"].items()}
        browsers = json.loads(Path(__file__).with_name("step_playwright_1_58.json").read_text())
        browser_source = (source / ("Dockerfile" if source.name in {"browser-use", "stagehand"} else "requirements.txt")).read_text()
        if "playwright==1.58.0" not in browser_source:
            raise ValueError("unreviewed Playwright browser transport version")
        return {arch: [metadata["assets"][arch], *[item for item in items
                       if source.name not in {"browser-use", "stagehand"} or "headless-shell" not in item["url"]]]
                for arch, items in browsers["assets"].items()}
    return {}


def instructions(text: str) -> list[tuple[str, str]]:
    lines = iter(text.splitlines())
    result = []
    for line in lines:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.match(r"^([A-Z]+)\s+(.*)$", line)
        if not match:
            raise ValueError("unsupported Dockerfile syntax")
        kind, value = match.groups()
        while value.endswith("\\"):
            value = value[:-1] + " " + next(lines).lstrip()
        heredoc = re.search(r"<<\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1", value)
        if heredoc:
            for body in lines:
                value += "\n" + body
                if body == heredoc[2]:
                    break
            else:
                raise ValueError("unterminated Dockerfile heredoc")
        result.append((kind, value))
    return result


def _copy(source: Path, value: str, workdir: str, source_commit: str | None = None) -> tuple[str, dict[str, str]]:
    words = shlex.split(value)
    owner = None
    if words and words[0].startswith("--chown="):
        owner = words.pop(0).split("=", 1)[1]
    if len(words) < 2 or any(word.startswith("--") for word in words):
        raise ValueError("COPY supports only explicit paths and --chown")
    destination = Path(words[-1])
    if not destination.is_absolute():
        destination = Path(workdir) / destination
    sources = words[:-1]
    directory = len(sources) > 1 or words[-1].endswith("/") or words[-1] in {".", "./"}
    files = []
    fetched = []
    hashes = {}
    for item in sources:
        if any(char in item for char in "*?["):
            raise ValueError("COPY globs are unsupported except the injected server wheel")
        path = source / item
        if not path.exists() or path.is_symlink() or not path.resolve().is_relative_to(source.resolve()):
            raise ValueError("COPY input is missing, symlinked or outside the template")
        paths = sorted(path.rglob("*")) if path.is_dir() else [path]
        for entry in paths:
            if entry.is_symlink():
                raise ValueError("symlinked COPY input is unsupported")
            if not entry.is_file():
                continue
            if entry.name == ".env" or entry.name.startswith(".env.") or entry.suffix in {".key", ".pem"}:
                raise ValueError("refusing a secret-named COPY input")
            data = entry.read_bytes()
            if len(data) > 2 * 1024 * 1024:
                raise ValueError("COPY input exceeds the 2 MiB per-file step limit")
            target = (destination / entry.relative_to(path) if path.is_dir() else
                      destination / entry.name if directory else destination)
            digest = hashlib.sha256(data).hexdigest()
            mode = entry.stat().st_mode & 0o777
            relative = str(entry.relative_to(source))
            can_fetch = False
            if source_commit:
                remote_path = source.name + "/" + relative
                previous = subprocess.run(["git", "show", source_commit + ":" + remote_path],
                                          cwd=source, capture_output=True)
                can_fetch = previous.returncode == 0 and previous.stdout == data
            if can_fetch:
                fetched.append([str(target), remote_path, digest, mode])
            else:
                files.append([str(target), base64.b64encode(data).decode(), mode])
            hashes[relative] = digest
    packed = base64.b64encode(zlib.compress(json.dumps(files).encode(), 9)).decode()
    fetch = ""
    if fetched:
        fetch = ("cache=Path('/tmp/abx-step-source-" + str(source_commit) + ".tar.gz')\n"
            "if not cache.exists():\n"
            " for attempt in range(4):\n"
            "  try:\n"
            "   request=urllib.request.Request('https://codeload.github.com/Alibaba-Agent-Sandbox/awesome-templates/tar.gz/"
            + str(source_commit) + "',headers={'User-Agent':'AgentSandbox-Template'})\n"
            "   archive=urllib.request.urlopen(request,timeout=90).read(33554433)\n"
            "   if len(archive)>33554432: raise RuntimeError('source archive exceeds 32 MiB')\n"
            "   cache.write_bytes(archive);break\n"
            "  except (urllib.error.URLError,TimeoutError):\n"
            "   if attempt==3: raise RuntimeError('pinned source archive download failed') from None\n"
            "   time.sleep(2**attempt)\n"
            "archive=tarfile.open(cache,mode='r:gz')\n"
            "for name,relative,digest,mode in " + repr(fetched) + ":\n"
            " data=archive.extractfile('awesome-templates-" + str(source_commit) + "/'+relative).read(2097153)\n"
            " if len(data)>2097152 or hashlib.sha256(data).hexdigest()!=digest: raise RuntimeError('immutable COPY integrity mismatch')\n"
            " files.append([name,base64.b64encode(data).decode(),mode])\n"
            "archive.close()\n")
    code = ("import base64,json,os,pwd,grp,zlib,urllib.request,urllib.error,hashlib,tarfile,time\nfrom pathlib import Path\n"
            "files=json.loads(zlib.decompress(base64.b64decode(" + repr(packed) + ")))\n" + fetch +
            "for name,data,mode in files:\n"
            " p=Path(name); p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(base64.b64decode(data)); p.chmod(mode)\n")
    if owner:
        if not re.fullmatch(r"[a-z_][a-z0-9_-]*:[a-z_][a-z0-9_-]*", owner):
            raise ValueError("COPY owner must be an explicit user:group")
        user, group = owner.split(":")
        code += f" os.chown(p,pwd.getpwnam({user!r}).pw_uid,grp.getgrnam({group!r}).gr_gid)\n"
    return "python3 -c " + shlex.quote(code), hashes


def compact_run(command: str) -> str:
    if len(command.encode()) < 1024:
        return command
    packed = base64.b64encode(zlib.compress(command.encode(), 9)).decode()
    code = ("import base64,zlib,os;os.execv('/bin/sh',['sh','-c',"
            "zlib.decompress(base64.b64decode(" + repr(packed) + ")).decode()])")
    compact = "python3 -c " + shlex.quote(code)
    return compact if len(compact.encode()) < len(command.encode()) else command


def prepare(source: Path, *, region: str = "cn-hangzhou", tag: str = "v0.0.49",
            server_commit: str | None = None, source_commit: str | None = None,
            base_path: str | None = None, asset_transport: str = "direct",
            asset_cache: dict | None = None,
            _inline: bool = True) -> tuple[dict, dict]:
    if asset_transport not in {"direct", "parallel", "oss"}:
        raise ValueError("asset transport must be direct, parallel or oss")
    if not re.fullmatch(r"[a-z]+-[a-z]+(?:-\d+)?", region) or not re.fullmatch(r"v\d+\.\d+\.\d+", tag):
        raise ValueError("use an explicit Alibaba region and versioned base tag")
    if server_commit is not None and not re.fullmatch(r"[0-9a-f]{40}", server_commit):
        raise ValueError("server source must be an immutable 40-character commit")
    source = source.resolve()
    opt_in = source / "server-sdk.commit"
    selected_server = pinned_server_commit(source) if opt_in.exists() or opt_in.is_symlink() else None
    if selected_server and server_commit is not None and server_commit != selected_server:
        raise ValueError("step server override differs from the required template SDK commit")
    if source_commit is None and source.parent == ROOT:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=source, capture_output=True, text=True)
        source_commit = head.stdout.strip() if head.returncode == 0 else None
    if source_commit is not None and not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        raise ValueError("source commit must be an immutable 40-character commit")
    data = yaml.safe_load((source / "template.yaml").read_text())
    if base_path is None and tag != "v0.0.49":
        raise ValueError("an unverified base tag requires an explicit verified --base-path")
    build_env = {"PATH": base_path or BASE_PATH}
    # Express executes steps as user by default; Docker's build profile installs
    # dependencies as root and explicitly returns to USER user for the runtime.
    steps = [{"type": "USER", "args": ["root"]}]
    copied = {"server-sdk.commit": hashlib.sha256(opt_in.read_bytes()).hexdigest()} if selected_server else {}
    workdir = "/"
    seen_from = False
    dockerfile = (source / "Dockerfile").read_text()
    def run_step(command: str) -> dict:
        # Native ENV configures the resulting runtime but did not affect RUN's
        # npm/PATH in the real platform probe. Recreate Docker build state explicitly.
        exports = "".join("export " + shlex.quote(key + "=" + val) + "\n" for key, val in build_env.items())
        directory = shlex.quote(workdir)
        return {"type": "RUN", "args": [exports + "mkdir -p " + directory + " || exit $?\ncd " + directory + " || exit $?\n" + command]}
    assets = parallel_assets(source) if asset_transport in {"parallel", "oss"} else {}
    public_assets = assets
    if assets and asset_transport == "oss":
        if not asset_cache or asset_cache.get("architecture") not in assets:
            raise ValueError("private OSS transport requires an owned architecture cache")
        arch = asset_cache["architecture"]
        # Short-lived authorization stays in the private execution manifest;
        # public source/provenance never contains cache URLs or identifiers.
        assets = {arch: [dict(item, transport_url=asset_cache["urls"][item["url"]])
                         for item in assets[arch]]}
    temporary_uv = asset_transport in {"parallel", "oss"} and source.name in {"deepagents", "osworld", "swe", "browser-use", "stagehand"}
    asset_root = "/tmp/abx-step-assets"
    uv_root = "/tmp/abx-step-installer"
    asset_helper = Path(__file__).with_name("step_assets.py")
    if assets and source.name == "hermes-agent":
        build_env["UV_PYTHON_INSTALL_MIRROR"] = "file://" + asset_root + "/python-mirror"
    if temporary_uv:
        build_env["UV_CACHE_DIR"] = uv_root + "/cache"
    if assets:
        files = {"step_assets.py": asset_helper.read_text(), "assets.json": json.dumps(assets)}
        fetch_helper = False
        if source_commit:
            published = subprocess.run(["git", "show", source_commit + ":scripts/step_assets.py"],
                                       cwd=source, capture_output=True)
            fetch_helper = published.returncode == 0 and published.stdout == asset_helper.read_bytes()
        if fetch_helper:
            del files["step_assets.py"]
        packed = base64.b64encode(zlib.compress(json.dumps(files).encode(), 9)).decode()
        bootstrap = ("import base64,json,zlib;from pathlib import Path;"
                     f"root=Path({asset_root!r});root.mkdir(mode=0o700);"
                     f"files=json.loads(zlib.decompress(base64.b64decode({packed!r})));"
                     "[(root/name).write_text(data) for name,data in files.items()]")
        if fetch_helper:
            url = "https://raw.githubusercontent.com/Alibaba-Agent-Sandbox/awesome-templates/" + source_commit + "/scripts/step_assets.py"
            digest = hashlib.sha256(asset_helper.read_bytes()).hexdigest()
            bootstrap += ("\nimport hashlib,time,urllib.request,urllib.error\n"
                          "for attempt in range(4):\n"
                          " try:\n"
                          f"  with urllib.request.urlopen({url!r},timeout=90) as response:data=response.read(32769)\n"
                          f"  if len(data)>32768 or hashlib.sha256(data).hexdigest()!={digest!r}:raise RuntimeError('immutable build adapter integrity mismatch')\n"
                          "  (root/'step_assets.py').write_bytes(data);break\n"
                          " except (urllib.error.URLError,TimeoutError):\n"
                          "  if attempt==3:raise RuntimeError('immutable build adapter download failed') from None\n"
                          "  time.sleep(2**attempt)\n")
        # Bootstrap/cache operations use only absolute owned paths and the
        # verified base Python, before any Dockerfile environment/workdir.
        steps.append({"type": "RUN", "args": ["python3 -c " + shlex.quote(bootstrap)]})
        for index in range(len(next(iter(assets.values())))):
            steps.append({"type": "RUN", "args": [f"python3 {asset_root}/step_assets.py fetch {index}"]})
    if temporary_uv:
        steps.append({"type": "RUN", "args": [f"python3 {asset_root}/step_assets.py install-uv"]})
    for kind, value in instructions(dockerfile):
        if kind == "FROM":
            if seen_from or value != BASE:
                raise ValueError("only the single-stage catalog Alibaba base profile is supported")
            seen_from = True
        elif kind == "COPY":
            if value == "*.whl /tmp/":
                continue  # Local source-wheel injection has no remote COPY context.
            command, hashes = _copy(source, value, workdir, None if _inline else source_commit)
            copied.update(hashes)
            steps.append(run_step(command))
        elif kind == "RUN":
            if temporary_uv and source.name in {"browser-use", "stagehand"}:
                if value == 'pip install --no-cache-dir "playwright==1.58.0"':
                    steps.append(run_step(f"{uv_root}/bin/uv --no-cache pip install --system --python python3 --default-index https://mirrors.aliyun.com/pypi/simple/ playwright==1.58.0"))
                    continue
                if value == "python3 -m playwright install chromium --no-shell":
                    steps.append(run_step(f"python3 {asset_root}/step_assets.py playwright " + value))
                    continue
            if assets:
                # The adapter exists only in these build Python processes. The
                # original installer bytes/limits/extraction/version checks stay.
                value = re.sub(r"(?<![\w/-])python3(?=\s+(?:-\s*<<|/tmp/))",
                               f"python3 {asset_root}/step_assets.py run", value)
            if assets and source.name == "hermes-agent" and "uv python install 3.14.6" in value:
                value = value.replace("uv python install 3.14.6", "uv python install cpython-3.14.6-linux-$(uname -m)-gnu")
                # The original compound RUN has one literal cd and no shell
                # exports/functions. Preserve that cwd across bounded phases.
                directory = "/"
                for part in re.split(r"\s+&&\s+", value):
                    if part.startswith("cd "):
                        directory = shlex.split(part)[1]
                    else:
                        if part == "pip install --no-cache-dir uv==0.12.3":
                            part = f"pip install --no-cache-dir --no-index --no-deps {asset_root}/uv-*.whl"
                        if part.startswith("curl -fsSL https://codeload.github.com/NousResearch/hermes-agent/"):
                            archive = next(item for item in next(iter(assets.values()))
                                           if item["url"].startswith("https://codeload.github.com/"))
                            part = f"tar -xz --strip-components=1 -C /opt/hermes -f {asset_root}/" + archive["sha256"]
                        steps.append(run_step("cd " + shlex.quote(directory) + " && " + part))
                continue
            if temporary_uv and ("--require-hashes" in value or source.name == "swe" and re.search(r"/opt/swe-(agent|eval)/bin/pip install", value)):
                for part in re.split(r"\s+&&\s+", value):
                    if "--require-hashes" in part or source.name == "swe" and re.match(r"/opt/swe-(agent|eval)/bin/pip install", part):
                        match = re.fullmatch(r"(/opt/[a-z-]+/bin/)(?:python -m pip|pip) install (.*)", part, re.S)
                        if not match:
                            raise ValueError("unreviewed locked Python package installation")
                        arguments = match[2].replace("--no-cache-dir", "")
                        if source.name in {"osworld", "browser-use"} and asset_transport == "oss":
                            # Keep every upstream version/hash and build rule;
                            # use the regional public PyPI mirror for transport.
                            arguments += " --default-index https://mirrors.aliyun.com/pypi/simple/"
                        part = f"{uv_root}/bin/uv --no-cache pip install --python {match[1]}python {arguments}"
                    if source.name == "osworld" and "-m playwright install --with-deps chromium" in part:
                        part = f"python3 {asset_root}/step_assets.py playwright " + part
                    steps.append(run_step(part))
                continue
            if "if ls /tmp/*.whl" in value:
                match = re.fullmatch(r"if ls /tmp/\*\.whl.*?; then\s+.*?else\s+(.*?)\s*;\s*fi(.*)", value, re.S)
                if not match:
                    raise ValueError("unknown server-wheel fallback; review it before generating steps")
                value = match[1] + match[2]
                if server_commit:
                    value, count = re.subn(r"(?<=python-sdk/archive/)[0-9a-f]{40}(?=\.tar\.gz)", server_commit, value)
                    if count != 1:
                        raise ValueError("expected one pinned server-source fallback")
            steps.append(run_step(value))
        elif kind == "WORKDIR":
            if not value.startswith("/"):
                raise ValueError("WORKDIR must be absolute")
            workdir = value
            steps.append({"type": kind, "args": [value]})
        elif kind == "ENV":
            pairs = []
            updates = {}
            for item in shlex.split(value):
                if "=" not in item:
                    raise ValueError("ENV requires explicit key=value declarations")
                key, val = item.split("=", 1)
                if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
                    raise ValueError("invalid ENV name")
                try:
                    val = Template(val).substitute(build_env)
                except (KeyError, ValueError):
                    raise ValueError("ENV references an unverified base variable") from None
                pairs.extend([key, val])
                updates[key] = val
            build_env.update(updates)
            steps.append({"type": kind, "args": pairs})
        elif kind == "USER":
            if value == "user" and workdir == "/home/user/app":
                # Native WORKDIR creates a root-owned directory. COPY file
                # ownership alone does not make that runtime directory writable.
                steps.append(run_step("chown user:user /home/user/app"))
            steps.append({"type": kind, "args": [value]})
        elif kind == "EXPOSE":
            continue  # Manifest ports and platform commands remain authoritative.
        else:
            raise ValueError(f"unsupported Docker instruction: {kind}")
    if not seen_from or not steps or steps[-1] != {"type": "USER", "args": ["user"]}:
        raise ValueError("the catalog profile must end with USER user")
    if not _inline and source_commit:
        steps.insert(len(steps) - 1, {"type": "RUN", "args": ["rm -f /tmp/abx-step-source-" + source_commit + ".tar.gz"]})
    cleanup = ([asset_root] if assets else []) + ([uv_root] if temporary_uv else [])
    if cleanup:
        steps.insert(len(steps) - 1, {"type": "RUN", "args": ["rm -rf " + " ".join(cleanup)]})
    for step in steps:
        if step["type"] == "RUN":
            step["args"] = [compact_run(step["args"][0])]
    wire_bytes = len(json.dumps(steps, ensure_ascii=False).encode())
    if wire_bytes > 15000:
        if _inline and source_commit:
            return prepare(source, region=region, tag=tag, server_commit=server_commit,
                           source_commit=source_commit, base_path=base_path,
                           asset_transport=asset_transport, asset_cache=asset_cache, _inline=False)
        raise ValueError(f"compressed steps ({wire_bytes} bytes) exceed the provider's 16 KiB limit; use an immutable source archive or Dockerfile mode")
    data["base"] = BASE.replace("<region>", region).replace("<tag>", tag)
    data["build"] = {"mode": "steps", "steps": steps}
    provenance = {"schema_version": 1, "template": source.name,
                  "materializer_sha256": MATERIALIZER_SHA256,
                  "source_manifest_contract_sha256": manifest_contract_sha256((source / "template.yaml").read_bytes()),
                  "template_version": str(data["version"]), "build_mode": "steps",
                  "base_image": data["base"], "server_commit_override": server_commit,
                  "template_server_commit": selected_server,
                  "verified_base_path": base_path or BASE_PATH,
                  "copy_source_commit": None if _inline else source_commit,
                  "asset_transport": asset_transport if assets else "parallel" if temporary_uv else "direct",
                  "steps_json_bytes": wire_bytes,
                  "inputs_sha256": {"Dockerfile": hashlib.sha256(dockerfile.encode()).hexdigest(),
                                    "template.yaml": hashlib.sha256((source / "template.yaml").read_bytes()).hexdigest(),
                                    **copied}}
    if assets:
        provenance["asset_transport_sha256"] = hashlib.sha256(asset_helper.read_bytes()).hexdigest()
        provenance["asset_adapter_source_commit"] = source_commit if fetch_helper else None
        provenance["build_assets"] = public_assets
        if asset_transport == "oss":
            provenance["asset_cache_architecture"] = asset_cache["architecture"]
        if source.name == "hermes-agent":
            provenance["python_download_profile"] = "uv0.12.3 generic GNU architecture; original Python3.14.6 pin, local verified official-archive mirror and bounded original compound-RUN phases"
    if temporary_uv:
        provenance["python_package_transport"] = "temporary uv0.12.3 installer; original package pins/requirements, retaining --require-hashes where declared; separate original compound-RUN phases; removed before runtime"
    manifest = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    if len(manifest.encode()) > 8 * 1024 * 1024:
        raise ValueError("generated step manifest exceeds the 8 MiB local safety limit")
    provenance["generated_manifest_sha256"] = hashlib.sha256(manifest.encode()).hexdigest()
    return data, provenance


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("template", type=Path)
    parser.add_argument("--output", required=True, type=Path, help="New standalone staging directory")
    parser.add_argument("--region", default="cn-hangzhou")
    parser.add_argument("--base-tag", default="v0.0.49")
    parser.add_argument("--base-path", help="Verified PATH when using a different base-image tag")
    parser.add_argument("--server-commit")
    parser.add_argument("--source-commit", help="Immutable public source; unchanged COPY files are fetched and hash-checked")
    parser.add_argument("--asset-transport", choices=("direct", "parallel"), default="direct")
    args = parser.parse_args()
    data, provenance = prepare(args.template, region=args.region, tag=args.base_tag,
                               server_commit=args.server_commit, source_commit=args.source_commit,
                               base_path=args.base_path, asset_transport=args.asset_transport)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "template.yaml").write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
    (args.output / "steps-provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(f"Prepared {args.template.name}: {len(data['build']['steps'])} explicit steps; no cloud call")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
