FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV WORKSPACE=/home/user/app

# Original npm artifact; exact integrity lock, no lifecycle scripts or optional image codecs.
COPY package.json package-lock.json /opt/claude-code/
RUN cd /opt/claude-code && npm ci --omit=optional --ignore-scripts --no-audit --no-fund \
    && ln -s /opt/claude-code/node_modules/.bin/claude /usr/local/bin/claude \
    && claude --version && npm cache clean --force \
    && mkdir -p /home/user/app && chown user:user /home/user/app

# The deploy CLI may inject a wheel; otherwise use the exact server commit.
COPY *.whl /tmp/
RUN if ls /tmp/*.whl 1>/dev/null 2>&1; then \
        pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl; \
    else \
        pip install --no-cache-dir "agent-sandbox-server @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/34e7e011c5569f77b7f605e65313be7498f6cf02.tar.gz#subdirectory=server-sdk"; \
    fi

WORKDIR /home/user/app
COPY --chown=user:user commands.py byok.py relay.py process.py lifecycle.py upstream.json .
RUN chown user:user /home/user/app
USER user
EXPOSE 9000
