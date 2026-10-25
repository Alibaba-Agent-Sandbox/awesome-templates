FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8
COPY install_runtime.py assets.json upstream-LICENSE /tmp/goose-build/
RUN python3 /tmp/goose-build/install_runtime.py --prefix /opt/goose && rm -rf /tmp/goose-build
ENV PATH="/opt/goose:${PATH}" HOME=/home/user WORKSPACE=/home/user/app
RUN pip install --no-cache-dir --index-url https://pypi.org/simple "agent-sandbox-server==0.4.0a2"
WORKDIR /home/user/app
COPY --chown=user:user commands.py .
RUN chown user:user /home/user/app \
    && python3 -c "import subprocess; used=int(subprocess.check_output(['du','-sx','--block-size=1','/']).split()[0]); assert used <= 8*1024**3, 'image rootfs exceeds8GiB'"
USER user
EXPOSE 9000
