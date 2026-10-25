FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV WORKSPACE=/home/user/workspace
ENV ABX_SERVER_POLICY_FILE=/home/user/app/server-policy.json

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates git ripgrep \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /home/user/app /home/user/workspace \
    && chown -R user:user /home/user/app /home/user/workspace
# Qwen Code 0.23.0 requires Node >=22; the base Node 20 is insufficient.
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
RUN npm install -g @openai/codex@0.162.1 @qwen-code/qwen-code@0.23.0 \
    && test "$(codex --version)" = "codex-cli 0.162.1" \
    && test "$(qwen --version)" = "0.23.0" \
    && npm cache clean --force

RUN pip install --no-cache-dir --index-url https://pypi.org/simple "agent-sandbox-server==0.4.0a6"

WORKDIR /home/user/app
COPY --chown=user:user commands.py server-policy.json ./
RUN chown user:user /home/user/app
USER user
EXPOSE 9000
