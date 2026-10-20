FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8
WORKDIR /opt/copilot
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts --omit=optional --no-audit --no-fund --registry=https://registry.npmjs.org \
    && npm cache clean --force \
    && test -x node_modules/@github/copilot-linux-x64/copilot \
    && test -f node_modules/@github/copilot/LICENSE.md
ENV PATH=/opt/copilot/node_modules/.bin:$PATH HOME=/home/user WORKSPACE=/home/user/app
COPY *.whl /tmp/
RUN if ls /tmp/*.whl 1>/dev/null 2>&1; then \
        pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl; \
    else \
        pip install --no-cache-dir "agent-sandbox-server @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/e2cb27e24fde0a67112f82b8d44af463445a5d1a.tar.gz#subdirectory=server-sdk"; \
    fi
WORKDIR /home/user/app
COPY --chown=user:user commands.py process.py lifecycle.py UPSTREAM-LICENSE.md ./
RUN chown user:user /home/user/app
USER user
EXPOSE 9000
