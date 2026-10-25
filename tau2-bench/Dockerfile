FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8
RUN python3 -c "import platform; assert platform.machine()=='x86_64', 'reviewed Tau2 profile is Linuxx64'"     && apt-get update && apt-get install -y --no-install-recommends ca-certificates git ripgrep     && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/tau2-bootstrap
COPY upstream.json /opt/tau2-bootstrap/upstream.json
COPY requirements.lock /opt/tau2-bootstrap/requirements.lock
COPY install_source.py /tmp/tau2-install.py
RUN python3 /tmp/tau2-install.py \
    && python3 -c "import sys; assert sys.version_info[:2] == (3,13), 'reviewed Python3.13 profile required'" \
    && python3 -m venv /opt/tau2-venv \
    && /opt/tau2-venv/bin/pip install --no-cache-dir --require-hashes -r /opt/tau2-bootstrap/requirements.lock \
    && /opt/tau2-venv/bin/pip check
RUN pip install --no-cache-dir --index-url https://pypi.org/simple "agent-sandbox-server==0.4.0a2"
ENV HOME=/home/user WORKSPACE=/home/user/workspace
WORKDIR /home/user/app
COPY --chown=user:user commands.py worker.py process.py lifecycle.py UPSTREAM-LICENSE.md AUDIOOP-LICENSE.txt ./
RUN mkdir -p /home/user/workspace && chown user:user /home/user/app /home/user/workspace     && python3 -c "import subprocess; p=subprocess.run(['du','-sx','--block-size=1','/'],capture_output=True,text=True,timeout=120); assert p.returncode==0; n=int(p.stdout.split()[0]); print('image_rootfs_bytes='+str(n)); assert n<=8*1024**3"
USER user
EXPOSE 9000
