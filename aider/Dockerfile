FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8

# Official aider-chat 0.86.2 requires Python >=3.10,<3.13. Keep the base's
# Python 3.13 for agent-sandbox-server and install Aider in a separate 3.12 venv.
# These are official python-build-standalone 20260211 release asset digests.
RUN python3 - <<'PYTHON'
import hashlib
from pathlib import Path
import platform
import tarfile
import urllib.request

checksums = {
    "x86_64": "1dbaa624a09e15afe7efbdac08d42993135a68db8d34f986ef6977a6d77bdc3c",
    "aarch64": "85fdc64fe672de7337198a63d89918037bf93bdb03480404d90f8f601abef1dd",
}
arch = platform.machine()
name = f"cpython-3.12.12+20260211-{arch}-unknown-linux-gnu-install_only_stripped.tar.gz"
archive = Path("/tmp/aider-python.tar.gz")
urllib.request.urlretrieve("https://github.com/astral-sh/python-build-standalone/releases/download/20260211/" + name, archive)
if hashlib.sha256(archive.read_bytes()).hexdigest() != checksums[arch]:
    raise RuntimeError("Aider Python archive SHA256 mismatch")
root = Path("/opt/aider-runtime")
root.mkdir(parents=True, exist_ok=True)
with tarfile.open(archive) as source:
    source.extractall(root, filter="data")
archive.unlink()
PYTHON
RUN /opt/aider-runtime/python/bin/python3.12 -m venv /opt/aider \
    && /opt/aider/bin/python -m pip install --no-cache-dir aider-chat==0.86.2 \
    && /opt/aider/bin/python -c 'import sys,importlib.metadata; assert sys.version_info[:3] == (3,12,12); assert importlib.metadata.version("aider-chat") == "0.86.2"' \
    && ln -s /opt/aider/bin/aider /usr/local/bin/aider

RUN pip install --no-cache-dir --index-url https://pypi.org/simple "agent-sandbox-server==0.4.0a6"

ENV WORKSPACE=/home/user/app PYTHON_DOTENV_DISABLED=1 LITELLM_LOCAL_MODEL_COST_MAP=True
WORKDIR /home/user/app
COPY --chown=user:user commands.py .
RUN chown user:user /home/user/app
USER user
EXPOSE 9000
