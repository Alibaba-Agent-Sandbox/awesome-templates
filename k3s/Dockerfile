FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>
ENV LANG=C.UTF-8
RUN python3 -c "import platform,sys; assert platform.machine()=='x86_64' and sys.version_info[:2]==(3,13)"
COPY upstream.json install_runtime.py UPSTREAM-LICENSE.md /tmp/k3s-original-installer/
RUN python3 /tmp/k3s-original-installer/install_runtime.py && rm -rf /tmp/k3s-original-installer && ln -s /opt/k3s/k3s /usr/local/bin/k3s
COPY *.whl /tmp/
RUN if ls /tmp/*.whl 1>/dev/null 2>&1; then \
        pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl; \
    else \
        pip install --no-cache-dir "agent-sandbox-server @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/34e7e011c5569f77b7f605e65313be7498f6cf02.tar.gz#subdirectory=server-sdk"; \
    fi
ENV HOME=/home/user WORKSPACE=/home/user/app
WORKDIR /home/user/app
COPY --chown=user:user commands.py runtime.py worker.py process.py lifecycle.py process_rpc.py lifecycle_rpc.py upstream.json UPSTREAM-LICENSE.md ./
RUN chown user:user /home/user/app && python3 -c "import subprocess; p=subprocess.run(['du','-sx','--block-size=1','/'],capture_output=True,text=True,timeout=120); assert p.returncode==0; n=int(p.stdout.split()[0]); print('image_rootfs_bytes='+str(n)); assert n<=8*1024**3"
USER user
EXPOSE 9000
