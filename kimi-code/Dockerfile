FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>

ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8
RUN python3 - <<'NODE'
import hashlib
from pathlib import Path
import platform
import tarfile
import time
import urllib.error
import urllib.request

architectures = {
    "x86_64": ("x64", "2faf6a387e9b62b888e21c54f01249fb27537ffecf1842f29f4c919d0a59a0ff"),
    "aarch64": ("arm64", "589f5b6dd4fcfee4dfda73013903c966abaa8abd93dbc9d436544e472b4f0e74"),
}
arch, expected = architectures[platform.machine()]
name = f"node-v24.16.0-linux-{arch}"
archive = Path("/tmp/node.tar.gz")
for attempt in range(4):
    try:
        with urllib.request.urlopen(f"https://nodejs.org/dist/v24.16.0/{name}.tar.gz", timeout=90) as response:
            content = response.read(100 * 1024 * 1024 + 1)
        if len(content) > 100 * 1024 * 1024:
            raise RuntimeError("Node archive exceeds expected size budget")
        archive.write_bytes(content)
        break
    except (urllib.error.URLError, TimeoutError):
        if attempt == 3:
            raise RuntimeError("pinned Node archive download failed") from None
        time.sleep(2 ** attempt)
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
RUN npm install -g @moonshot-ai/kimi-code@2.2.0 && kimi --version && npm cache clean --force

RUN pip install --no-cache-dir --index-url https://pypi.org/simple "agent-sandbox-server==0.4.0a6"

WORKDIR /home/user/app
COPY --chown=user:user commands.py .
RUN chown user:user /home/user/app
USER user
EXPOSE 9000
