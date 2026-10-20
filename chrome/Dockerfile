FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8
RUN python3 -c "import sys,platform; assert sys.version_info[:2]==(3,13) and platform.machine()=='x86_64', 'reviewed Linuxx64 Python3.13 profile required'" \
    && apt-get update && apt-get install -y --no-install-recommends \
       ca-certificates xvfb=2:21.1.16-1.3+deb13u4 openbox=3.6.1-12+b2 \
       xauth=1:1.1.2-1.1 x11vnc=0.9.17-1 novnc=1:1.6.0-2 \
       tigervnc-tools=1.15.0+dfsg-2.1~deb13u1 fonts-dejavu-core=2.37-8 x11-utils=7.7+7 \
       libasound2t64 libatk-bridge2.0-0t64 libatk1.0-0t64 libatspi2.0-0t64 \
       libcairo2 libcups2t64 libdbus-1-3 libdrm2 libgbm1 libglib2.0-0t64 \
       libnspr4 libnss3 libpango-1.0-0 libx11-6 libxcb1 libxcomposite1 \
       libxdamage1 libxext6 libxfixes3 libxkbcommon0 libxrandr2 \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.lock /tmp/chrome-requirements.lock
RUN python3 -m venv /opt/chrome \
    && /opt/chrome/bin/pip install --no-cache-dir --require-hashes -r /tmp/chrome-requirements.lock \
    && /opt/chrome/bin/pip check && rm /tmp/chrome-requirements.lock
COPY browser.json /opt/chrome/browser.json
COPY install_browser.py /tmp/chrome-install.py
RUN python3 /tmp/chrome-install.py && rm /tmp/chrome-install.py
COPY *.whl /tmp/
RUN if ls /tmp/*.whl 1>/dev/null 2>&1; then \
        pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl; \
    else \
        pip install --no-cache-dir "agent-sandbox-server @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/e2cb27e24fde0a67112f82b8d44af463445a5d1a.tar.gz#subdirectory=server-sdk"; \
    fi
ENV HOME=/home/user WORKSPACE=/home/user/workspace
WORKDIR /home/user/app
COPY --chown=user:user commands.py worker.py native.py cdp.py rfb.py relay.py process.py lifecycle.py UPSTREAM-NOTICE.md ./
RUN mkdir -p /home/user/workspace && chown user:user /home/user/app /home/user/workspace \
    && python3 -c "import subprocess; p=subprocess.run(['du','-sx','--block-size=1','/'],capture_output=True,text=True,timeout=120); assert p.returncode==0; n=int(p.stdout.split()[0]); print('image_rootfs_bytes='+str(n)); assert n<=8*1024**3"
USER user
EXPOSE 9000 9222 6080
