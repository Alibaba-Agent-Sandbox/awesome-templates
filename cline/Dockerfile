FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8
RUN python3 -c "import platform; assert platform.machine()=='x86_64', 'reviewed Cline profile is Linuxx64'"     && apt-get update && apt-get install -y --no-install-recommends ca-certificates git ripgrep     && rm -rf /var/lib/apt/lists/*
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
WORKDIR /opt/cline
COPY package.json package-lock.json ./
RUN npm ci --omit=dev --ignore-scripts --no-audit --no-fund     && python3 -c "import hashlib,pathlib; p=pathlib.Path('/opt/cline/node_modules/@cline/cli-linux-x64/bin/cline'); assert hashlib.file_digest(p.open('rb'),'sha256').hexdigest()=='1ff8841d17d4d83763134c193d414e4f7fcf2ef56af759e5ebbe96727fc2c8f7'"     && npm cache clean --force
RUN pip install --no-cache-dir --index-url https://pypi.org/simple "agent-sandbox-server==0.4.0a4"
ENV HOME=/home/user WORKSPACE=/home/user/workspace
WORKDIR /home/user/app
COPY --chown=user:user commands.py process.py lifecycle.py UPSTREAM-LICENSE.md ./
RUN mkdir -p /home/user/workspace && chown user:user /home/user/app /home/user/workspace     && python3 -c "import subprocess; p=subprocess.run(['du','-sx','--block-size=1','/'],capture_output=True,text=True,timeout=120); assert p.returncode==0; n=int(p.stdout.split()[0]); print('image_rootfs_bytes='+str(n)); assert n<=8*1024**3"
USER user
EXPOSE 9000
