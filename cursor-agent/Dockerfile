FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>
ENV LANG=C.UTF-8
RUN python3 -c "import platform,sys; assert platform.machine()=='x86_64' and sys.version_info[:2]==(3,13)" && command -v bash && command -v git
COPY upstream.json install_runtime.py /tmp/cursor-original-installer/
RUN python3 /tmp/cursor-original-installer/install_runtime.py && rm -rf /tmp/cursor-original-installer && ln -s /opt/cursor-agent/cursor-agent /usr/local/bin/agent
RUN pip install --no-cache-dir --index-url https://pypi.org/simple "agent-sandbox-server==0.4.0a4"
ENV HOME=/home/user WORKSPACE=/home/user/app
WORKDIR /home/user/app
COPY --chown=user:user commands.py runtime.py process.py lifecycle.py upstream.json UPSTREAM-NOTICE.md ./
RUN chown user:user /home/user/app && python3 -c "import subprocess; p=subprocess.run(['du','-sx','--block-size=1','/'],capture_output=True,text=True,timeout=120); assert p.returncode==0; n=int(p.stdout.split()[0]); print('image_rootfs_bytes='+str(n)); assert n<=8*1024**3"
USER user
EXPOSE 9000
