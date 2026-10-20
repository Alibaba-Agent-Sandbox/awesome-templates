FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8
RUN python3 -m venv /opt/swe-agent \
    && /opt/swe-agent/bin/pip install --no-cache-dir mini-swe-agent==2.4.6 litellm==1.82.6 \
    && /opt/swe-agent/bin/python -c 'import importlib.metadata as m; assert m.version("mini-swe-agent") == "2.4.6"' \
    && ln -s /opt/swe-agent/bin/mini /usr/local/bin/mini
# Flask's unchanged tests treat pkgutil.get_loader's Python 3.13 deprecation
# as an error. Pin the instance's original Python 3.11.10 independently; keep
# the base server and mini agent on Python 3.13. Official release asset hashes.
RUN python3 - <<'PYTHON'
import hashlib
from pathlib import Path
import platform
import tarfile
import urllib.request
checksums = {
    "x86_64": "03f15e19e2452641b6375b59ba094ff6cf2fc118315d24a6ca63ce60e4d4a6e0",
    "aarch64": "9d124604ffdea4fbaabb10b343c5a36b636a3e7b94dfc1cccd4531f33fceae5e",
}
arch = platform.machine()
name = f"cpython-3.11.10+20241016-{arch}-unknown-linux-gnu-install_only_stripped.tar.gz"
archive = Path("/tmp/swe-python.tar.gz")
with urllib.request.urlopen("https://github.com/astral-sh/python-build-standalone/releases/download/20241016/" + name, timeout=120) as response:
    archive.write_bytes(response.read(40 * 1024 * 1024))
if hashlib.sha256(archive.read_bytes()).hexdigest() != checksums[arch]:
    raise RuntimeError("SWE evaluation Python archive SHA256 mismatch")
root = Path("/opt/swe-python"); root.mkdir(parents=True, exist_ok=True)
with tarfile.open(archive) as source:
    source.extractall(root, filter="data")
archive.unlink()
PYTHON
RUN /opt/swe-python/python/bin/python3.11 -m venv /opt/swe-eval \
    && /opt/swe-eval/bin/pip install --no-cache-dir pytest==8.3.5 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.2 Werkzeug==2.3.8 Jinja2==3.1.6 MarkupSafe==3.0.3 itsdangerous==2.2.0 click==8.1.8 blinker==1.9.0 asgiref==3.8.1 \
    && /opt/swe-eval/bin/python -c 'import sys; assert sys.version_info[:3] == (3,11,10)'
RUN mkdir -p /opt/swe && python3 - <<'PY'
import hashlib, pathlib, urllib.request
p=pathlib.Path('/opt/swe/flask_base.tar.gz')
url='https://codeload.github.com/pallets/flask/tar.gz/7ee9ceb71e868944a46e1ff00b506772a53a4f1d'
with urllib.request.urlopen(url, timeout=120) as response:
    p.write_bytes(response.read(2 * 1024 * 1024))
assert hashlib.sha256(p.read_bytes()).hexdigest() == 'b1a4c83b7d12981b81e5f8d2028a73eacfbd153f4e425504c254a6f177b99997'
PY
COPY *.whl /tmp/
RUN if ls /tmp/*.whl 1>/dev/null 2>&1; then \
        pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl; \
    else \
        pip install --no-cache-dir "agent-sandbox-server @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/e2cb27e24fde0a67112f82b8d44af463445a5d1a.tar.gz#subdirectory=server-sdk"; \
    fi
ENV WORKSPACE=/home/user/app PYTHON_DOTENV_DISABLED=1
WORKDIR /home/user/app
COPY --chown=user:user commands.py swe_process.py swe_environment.py instance.json ./
RUN chown user:user /home/user/app
USER user
EXPOSE 9000
