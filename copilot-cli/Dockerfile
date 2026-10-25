FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8
WORKDIR /opt/copilot
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts --omit=optional --no-audit --no-fund --registry=https://registry.npmjs.org \
    && npm cache clean --force \
    && test -x node_modules/@github/copilot-linux-x64/copilot \
    && test -f node_modules/@github/copilot/LICENSE.md
ENV PATH=/opt/copilot/node_modules/.bin:$PATH HOME=/home/user WORKSPACE=/home/user/app
RUN pip install --no-cache-dir --index-url https://pypi.org/simple "agent-sandbox-server==0.4.0a6"
WORKDIR /home/user/app
COPY --chown=user:user commands.py process.py lifecycle.py UPSTREAM-LICENSE.md ./
RUN chown user:user /home/user/app
USER user
EXPOSE 9000
