FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8
RUN python3 -c "import sys,platform; assert sys.version_info[:2]==(3,13) and platform.machine()=='x86_64', 'reviewed Linuxx64 Python3.13 required'" \
    && apt-get update && apt-get install -y --no-install-recommends ca-certificates git libgomp1 \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.lock /tmp/prime-kernel.lock
RUN python3 -m venv /opt/prime-kernel \
    && /opt/prime-kernel/bin/pip install --no-cache-dir --require-hashes -r /tmp/prime-kernel.lock \
    && /opt/prime-kernel/bin/pip check && rm /tmp/prime-kernel.lock
COPY upstream.json /opt/prime-bootstrap/upstream.json
COPY install_native.py /tmp/prime-native-install.py
RUN python3 /tmp/prime-native-install.py && rm /tmp/prime-native-install.py \
    && ln -s /opt/prime-agent/prime-agent /usr/local/bin/prime-agent
COPY kernel-python /opt/prime-kernel/bin/abx-kernel-python
RUN chmod 755 /opt/prime-kernel/bin/abx-kernel-python \
    && chmod -R a+rX /opt/prime-agent /opt/prime-kernel \
    && /opt/prime-kernel/bin/abx-kernel-python -c "import rlm,rlm.repl; assert rlm.repl.PROTOCOL_VERSION==3; assert all(callable(getattr(rlm,n,None)) for n in ['spawn','create_session','host_request','progress_note','rename']); import requests,httpx,yaml,tomli,dotenv,pandas,numpy,scipy,bs4,lxml,pydantic,tyro,dill; print('Original Prime CPython runtime protocol3 and locked required imports OK')"
RUN pip install --no-cache-dir --index-url https://pypi.org/simple "agent-sandbox-server==0.4.0a3"
ENV HOME=/home/user WORKSPACE=/home/user/workspace
WORKDIR /home/user/app
COPY --chown=user:user commands.py filter_native.py process.py lifecycle.py UPSTREAM-NOTICE.md ./
RUN mkdir -p /home/user/workspace && chown user:user /home/user/app /home/user/workspace \
    && python3 -c "import subprocess; p=subprocess.run(['du','-sx','--block-size=1','/'],capture_output=True,text=True,timeout=120); assert p.returncode==0; n=int(p.stdout.split()[0]); print('image_rootfs_bytes='+str(n)); assert n<=8*1024**3"
USER user
EXPOSE 9000
