FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright

# Playwright pins its Chromium revision; install system libraries during image build.
RUN pip install --no-cache-dir "playwright==1.58.0"
RUN python3 -m playwright install-deps chromium
RUN python3 -m playwright install chromium

RUN pip install --no-cache-dir --index-url https://pypi.org/simple "agent-sandbox-server==0.4.0a4"

COPY package.json package-lock.json /opt/playwright-mcp/
RUN cd /opt/playwright-mcp && PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm ci --ignore-scripts --omit=dev --no-audit --no-fund

WORKDIR /home/user/app
COPY --chown=user:user commands.py mcp_runtime.py mcp_process.py browser_process.py pdf_worker.py .
RUN chown user:user /home/user/app
RUN python3 -c "import subprocess; p=subprocess.run(['du','-sx','--block-size=1','/'],capture_output=True,text=True,timeout=120); assert p.returncode==0, 'rootfs accounting failed'; n=int(p.stdout.split()[0]); print('image_rootfs_bytes='+str(n)); assert n<=8*1024**3, 'rootfs exceeds8GiB'"
USER user
EXPOSE 9000
