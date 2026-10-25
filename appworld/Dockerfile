FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8
RUN python3 -c "import sys,platform; assert sys.version_info[:2]==(3,13) and platform.machine()=='x86_64', 'reviewed Linuxx64 Python3.13 required'"
COPY requirements-build.lock /tmp/appworld-build.lock
RUN python3 -m venv /opt/appworld-venv \
    && PIP_ONLY_BINARY=:all: /opt/appworld-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/appworld-build.lock \
    && rm /tmp/appworld-build.lock
COPY requirements.lock /tmp/appworld-requirements.lock
RUN DISABLE_SQLALCHEMY_CEXT=1 PIP_NO_BUILD_ISOLATION=false /opt/appworld-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/appworld-requirements.lock \
    && /opt/appworld-venv/bin/pip check && rm /tmp/appworld-requirements.lock
COPY upstream.json /opt/appworld-bootstrap/upstream.json
COPY install_data.py /tmp/appworld-install-data.py
RUN python3 /tmp/appworld-install-data.py && rm /tmp/appworld-install-data.py \
    && chmod -R a+rX /opt/appworld-bootstrap /opt/appworld-venv
RUN pip install --no-cache-dir --index-url https://pypi.org/simple "agent-sandbox-server==0.4.0a2"
ENV HOME=/home/user WORKSPACE=/home/user/workspace
WORKDIR /home/user/app
COPY --chown=user:user commands.py worker.py install_data.py process.py lifecycle.py UPSTREAM-NOTICE.md ./
RUN mkdir -p /home/user/workspace && chown user:user /home/user/app /home/user/workspace \
    && python3 -c "import subprocess; p=subprocess.run(['du','-sx','--block-size=1','/'],capture_output=True,text=True,timeout=120); assert p.returncode==0; n=int(p.stdout.split()[0]); print('image_rootfs_bytes='+str(n)); assert n<=8*1024**3"
USER user
EXPOSE 9000
