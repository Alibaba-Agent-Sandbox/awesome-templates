FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV HOME=/home/user
ENV FACTORY_DROID_AUTO_UPDATE_ENABLED=false
ENV WORKSPACE=/home/user/app

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates git ripgrep \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /home/user/app \
    && chown -R user:user /home/user

RUN python3 -c "import platform; assert platform.machine()=='x86_64', 'reviewed Droid native profile requires Linuxx64'"
WORKDIR /opt/droid
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts --omit=dev --include=optional --no-audit --no-fund --registry=https://registry.npmjs.org \
    && python3 -c "import hashlib,pathlib; p=pathlib.Path('/opt/droid/node_modules/@factory/cli-linux-x64/bin/droid'); assert hashlib.file_digest(p.open('rb'),'sha256').hexdigest()=='1f50e238df053573aec1dae7b90b19c8e5afca83ab13a790a00f53ba4e4b9ab1'" \
    && ln -s /opt/droid/node_modules/@factory/cli-linux-x64/bin/droid /usr/local/bin/droid \
    && test "$(droid --version)" = "0.241.1" \
    && npm cache clean --force

RUN pip install --no-cache-dir "agent-sandbox-server==0.4.0a2"

WORKDIR /home/user/app
COPY --chown=user:user commands.py byok.py process.py lifecycle.py UPSTREAM-NOTICE.md ./
RUN chown user:user /home/user/app \
    && python3 -c "import subprocess; p=subprocess.run(['du','-sx','--block-size=1','/'],capture_output=True,text=True,timeout=120); assert p.returncode==0; n=int(p.stdout.split()[0]); print('image_rootfs_bytes='+str(n)); assert n<=8*1024**3"
USER user
EXPOSE 9000
