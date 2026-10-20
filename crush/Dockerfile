FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8
COPY install_runtime.py assets.json upstream-LICENSE.md /tmp/crush-build/
RUN python3 /tmp/crush-build/install_runtime.py --prefix /opt/crush && rm -rf /tmp/crush-build
ENV PATH="/opt/crush:${PATH}" HOME=/home/user WORKSPACE=/home/user/app
COPY *.whl /tmp/
RUN if ls /tmp/*.whl 1>/dev/null 2>&1; then \
        pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl; \
    else \
        pip install --no-cache-dir "agent-sandbox-server @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/e2cb27e24fde0a67112f82b8d44af463445a5d1a.tar.gz#subdirectory=server-sdk"; \
    fi
WORKDIR /home/user/app
COPY --chown=user:user commands.py process.py lifecycle.py .
RUN chown user:user /home/user/app \
    && python3 -c "import subprocess; used=int(subprocess.check_output(['du','-sx','--block-size=1','/']).split()[0]); assert used <= 8*1024**3, 'image rootfs exceeds8GiB'"
USER user
EXPOSE 9000
