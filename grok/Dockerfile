FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8
RUN python3 -c "import platform; assert platform.machine()=='x86_64', 'reviewed Grok profile is Linuxx64'"     && apt-get update && apt-get install -y --no-install-recommends ca-certificates git ripgrep     && rm -rf /var/lib/apt/lists/*
RUN python3 - <<'NODE'
import hashlib
from pathlib import Path
import platform
import tarfile
import urllib.request

architectures = {
    "x86_64": ("x64", "2faf6a387e9b62b888e21c54f01249fb27537ffecf1842f29f4c919d0a59a0ff"),
    "aarch64": ("arm64", "589f5b6dd4fcfee4dfda73013903c966abaa8abd93dbc9d436544e472b4f0e74"),
}
arch, expected = architectures[platform.machine()]
name = f"node-v24.16.0-linux-{arch}"
archive = Path("/tmp/node.tar.gz")
urllib.request.urlretrieve(f"https://nodejs.org/dist/v24.16.0/{name}.tar.gz", archive)
if hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
    raise RuntimeError("Node archive SHA256 mismatch")
root = Path("/opt/node")
root.mkdir(parents=True, exist_ok=True)
with tarfile.open(archive) as source:
    source.extractall(root, filter="data")
(root / "current").symlink_to(root / name)
archive.unlink()
NODE
ENV PATH="/opt/node/current/bin:${PATH}"
WORKDIR /opt/grok
COPY package.json package-lock.json ./
RUN npm ci --omit=dev --ignore-scripts --no-audit --no-fund \
    && mkdir -p /opt/grok/bin \
    && node -e "const f=require('fs'),z=require('zlib');f.writeFileSync('/opt/grok/bin/grok',z.brotliDecompressSync(f.readFileSync('/opt/grok/node_modules/@xai-official/grok-linux-x64/bin/grok.br')))" \
    && chmod 755 /opt/grok/bin/grok \
    && python3 -c "import hashlib,pathlib; p=pathlib.Path('/opt/grok/bin/grok'); assert hashlib.file_digest(p.open('rb'),'sha256').hexdigest()=='2a46d9e4d7ebd7a9cff7f95716714b19dad5f21dd2a497822400b1fb128969aa'" \
    && npm cache clean --force
RUN pip install --no-cache-dir --index-url https://pypi.org/simple "agent-sandbox-server==0.4.0a6"
ENV HOME=/home/user WORKSPACE=/home/user/workspace
WORKDIR /home/user/app
COPY --chown=user:user commands.py process.py lifecycle.py UPSTREAM-LICENSE.md THIRD_PARTY_NOTICES.md ./
RUN mkdir -p /home/user/workspace && chown user:user /home/user/app /home/user/workspace     && python3 -c "import subprocess; p=subprocess.run(['du','-sx','--block-size=1','/'],capture_output=True,text=True,timeout=120); assert p.returncode==0; n=int(p.stdout.split()[0]); print('image_rootfs_bytes='+str(n)); assert n<=8*1024**3"
USER user
EXPOSE 9000
