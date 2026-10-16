FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8
RUN python3 -m venv /opt/swe-agent \
    && /opt/swe-agent/bin/pip install --no-cache-dir mini-swe-agent==2.4.6 litellm==1.82.6 \
    && /opt/swe-agent/bin/python -c 'import importlib.metadata as m; assert m.version("mini-swe-agent") == "2.4.6"' \
    && ln -s /opt/swe-agent/bin/mini /usr/local/bin/mini
RUN python3 -m venv /opt/swe-eval \
    && /opt/swe-eval/bin/pip install --no-cache-dir pytest==8.3.5 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.2 Werkzeug==2.3.8 Jinja2==3.1.6 MarkupSafe==3.0.3 itsdangerous==2.2.0 click==8.1.8 blinker==1.9.0 asgiref==3.8.1
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
USER user
EXPOSE 9000
