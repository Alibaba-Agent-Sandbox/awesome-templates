FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8 PLAYWRIGHT_BROWSERS_PATH=/opt/playwright
RUN pip install --no-cache-dir "playwright==1.58.0"
RUN python3 -m playwright install-deps chromium
RUN python3 -m playwright install chromium --no-shell
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
WORKDIR /home/user/app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev --ignore-scripts     && node --input-type=module -e "import fs from 'node:fs'; const p=JSON.parse(fs.readFileSync('node_modules/@browserbasehq/stagehand/package.json')); if(p.version!=='4.3.0')process.exit(1); await import('@browserbasehq/stagehand')"     && npm cache clean --force
COPY patch_sdk.py /tmp/patch-stagehand-sdk.py
RUN python3 /tmp/patch-stagehand-sdk.py /home/user/app/node_modules/@browserbasehq/stagehand/dist/index.mjs \
    && rm /tmp/patch-stagehand-sdk.py
RUN pip install --no-cache-dir --index-url https://pypi.org/simple "agent-sandbox-server==0.4.0a2"
ENV HOME=/home/user WORKSPACE=/home/user/app
COPY --chown=user:user commands.py worker.mjs browser.mjs transport.mjs process.py lifecycle.py UPSTREAM-LICENSE.md ./
RUN chown user:user /home/user/app     && python3 -c "import subprocess; p=subprocess.run(['du','-sx','--block-size=1','/'],capture_output=True,text=True,timeout=120); assert p.returncode==0; n=int(p.stdout.split()[0]); print('image_rootfs_bytes='+str(n)); assert n<=8*1024**3"
USER user
EXPOSE 9000
