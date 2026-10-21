FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>

ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8
# Original official integrity-locked package; optional interactive native add-ons omitted.
COPY package.json package-lock.json /opt/gemini/
RUN cd /opt/gemini && npm ci --omit=optional --ignore-scripts --no-audit --no-fund \
    && ln -s /opt/gemini/node_modules/.bin/gemini /usr/local/bin/gemini \
    && gemini --version && npm cache clean --force

COPY *.whl /tmp/
RUN if ls /tmp/*.whl 1>/dev/null 2>&1; then \
        pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl; \
    else \
        pip install --no-cache-dir "agent-sandbox-server @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/34e7e011c5569f77b7f605e65313be7498f6cf02.tar.gz#subdirectory=server-sdk"; \
    fi

ENV HOME=/home/user WORKSPACE=/home/user/app GEMINI_MODEL=gemini-3.1-flash-lite
WORKDIR /home/user/app
COPY --chown=user:user commands.py byok.py relay.py process.py lifecycle.py upstream.json .
RUN chown user:user /home/user/app
USER user
EXPOSE 9000
