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
RUN pip install --no-cache-dir --index-url https://pypi.org/simple "agent-sandbox-server==0.4.0a3"

WORKDIR /home/user/app
COPY --chown=user:user commands.py byok.py relay.py process.py lifecycle.py upstream.json .
RUN chown user:user /home/user/app
USER user
EXPOSE 9000
