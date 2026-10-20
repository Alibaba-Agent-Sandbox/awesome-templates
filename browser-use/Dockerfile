FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8 PLAYWRIGHT_BROWSERS_PATH=/opt/playwright
RUN pip install --no-cache-dir "playwright==1.58.0"
RUN python3 -m playwright install-deps chromium
RUN python3 -m playwright install chromium --no-shell
COPY requirements.lock /tmp/browser-use-requirements.lock
RUN python3 -c "import sys; assert sys.version_info[:2] == (3,13), 'reviewed Python3.13 profile required'" \
    && python3 -m venv /opt/browser-use \
    && /opt/browser-use/bin/python -m pip install --no-cache-dir --require-hashes -r /tmp/browser-use-requirements.lock \
    && /opt/browser-use/bin/python -m pip check \
    && /opt/browser-use/bin/python -c "from importlib.metadata import version; assert version('browser-use') == '0.13.11'" \
    && rm /tmp/browser-use-requirements.lock
COPY *.whl /tmp/
RUN if ls /tmp/*.whl 1>/dev/null 2>&1; then \
        pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl; \
    else \
        pip install --no-cache-dir "agent-sandbox-server @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/e2cb27e24fde0a67112f82b8d44af463445a5d1a.tar.gz#subdirectory=server-sdk"; \
    fi
ENV HOME=/home/user WORKSPACE=/home/user/app BROWSER_USE_PYTHON=/opt/browser-use/bin/python
WORKDIR /home/user/app
COPY --chown=user:user commands.py worker.py process.py lifecycle.py .
RUN chown user:user /home/user/app \
    && python3 -c "import subprocess; p=subprocess.run(['du','-sx','--block-size=1','/'],capture_output=True,text=True,timeout=120); assert p.returncode==0, 'rootfs accounting failed'; n=int(p.stdout.split()[0]); print('image_rootfs_bytes='+str(n)); assert n<=8*1024**3, 'rootfs exceeds8GiB'"
USER user
EXPOSE 9000
