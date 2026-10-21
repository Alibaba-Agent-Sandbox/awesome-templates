FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8
RUN python3 -c "import platform,sys; assert platform.machine()=='x86_64' and sys.version_info[:2]==(3,13), 'reviewed Linuxx64/Python3.13 required'" \
    && apt-get update && apt-get install -y --no-install-recommends ca-certificates git ripgrep \
    && rm -rf /var/lib/apt/lists/*
COPY upstream.json /opt/qm-bootstrap/upstream.json
COPY install_runtime.py /tmp/qm-original-install.py
RUN python3 /tmp/qm-original-install.py && rm /tmp/qm-original-install.py
ENV PATH="/opt/node/current/bin:${PATH}"
COPY package.json package-lock.json sdk-package.json sdk-package-lock.json /tmp/qm-review-locks/
RUN python3 -c "from pathlib import Path; mapping={'package.json':'/opt/qm/package.json','package-lock.json':'/opt/qm/package-lock.json','sdk-package.json':'/opt/agent-sandbox-node-sdk/package.json','sdk-package-lock.json':'/opt/agent-sandbox-node-sdk/package-lock.json'}; assert all((Path('/tmp/qm-review-locks')/name).read_bytes()==Path(target).read_bytes() for name,target in mapping.items()), 'original source and reviewed locks differ'" \
    && rm -rf /tmp/qm-review-locks \
    && NODE_OPTIONS=--use-system-ca npm ci --prefix /opt/agent-sandbox-node-sdk --ignore-scripts --no-audit --no-fund --registry=https://registry.npmjs.org \
    && npm run build --prefix /opt/agent-sandbox-node-sdk \
    && NODE_OPTIONS=--use-system-ca npm ci --prefix /opt/qm --ignore-scripts --no-audit --no-fund --registry=https://registry.npmjs.org \
    && npm cache clean --force \
    && chmod -R a+rX /opt/node /opt/qm /opt/agent-sandbox-node-sdk /opt/qm-bootstrap
COPY *.whl /tmp/
RUN if ls /tmp/*.whl 1>/dev/null 2>&1; then \
        pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl; \
    else \
        pip install --no-cache-dir "agent-sandbox-server @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/34e7e011c5569f77b7f605e65313be7498f6cf02.tar.gz#subdirectory=server-sdk"; \
    fi
ENV HOME=/home/user WORKSPACE=/home/user/app QM_SANDBOX_BASE_URL=http://127.0.0.1:9000
WORKDIR /home/user/app
COPY --chown=user:user commands.py worker.mjs adapter.mjs sdk_path.py sdk_exec.py process.py tool_process.py lifecycle.py UPSTREAM-NOTICE.md ./
RUN chown user:user /home/user/app \
    && python3 -c "import subprocess; p=subprocess.run(['du','-sx','--block-size=1','/'],capture_output=True,text=True,timeout=120); assert p.returncode==0; n=int(p.stdout.split()[0]); print('image_rootfs_bytes='+str(n)); assert n<=8*1024**3"
USER user
EXPOSE 9000
