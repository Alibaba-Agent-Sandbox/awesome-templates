FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8 NEXT_TELEMETRY_DISABLED=1
COPY package.json package-lock.json /opt/next-app/
RUN npm ci --prefix /opt/next-app --ignore-scripts --no-audit --no-fund && npm cache clean --force
COPY *.whl /tmp/
RUN if ls /tmp/*.whl 1>/dev/null 2>&1; then \
        pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl; \
    else \
        pip install --no-cache-dir "agent-sandbox-server @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/e2cb27e24fde0a67112f82b8d44af463445a5d1a.tar.gz#subdirectory=server-sdk"; \
    fi

WORKDIR /home/user/app
COPY --chown=user:user commands.py lifecycle.py .
RUN chown user:user /home/user/app
USER user
EXPOSE 9000 3000 5173
