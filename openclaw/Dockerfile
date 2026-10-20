FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>

# The base includes Node 20; this pinned OpenClaw requires Node >=24.16.
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
RUN node --version \
    && npm install -g openclaw@2026.10.4 \
    && openclaw --version \
    && npm cache clean --force
COPY *.whl /tmp/
RUN if ls /tmp/*.whl 1>/dev/null 2>&1; then \
        pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl; \
    else \
        pip install --no-cache-dir "agent-sandbox-server @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/35da216a300f1e2e84254a1cf4b4a7ea98681505.tar.gz#subdirectory=server-sdk"; \
    fi
WORKDIR /home/user/app
COPY --chown=user:user commands.py .
RUN chown user:user /home/user/app
USER user
EXPOSE 9000 18789
