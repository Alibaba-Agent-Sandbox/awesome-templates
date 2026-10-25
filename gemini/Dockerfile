FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>

ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8
# Original official integrity-locked package; optional interactive native add-ons omitted.
COPY package.json package-lock.json /opt/gemini/
RUN cd /opt/gemini && npm ci --omit=optional --ignore-scripts --no-audit --no-fund \
    && ln -s /opt/gemini/node_modules/.bin/gemini /usr/local/bin/gemini \
    && gemini --version && npm cache clean --force

COPY profile.json /opt/gemini/profile.json
RUN chmod 0644 /opt/gemini/profile.json

RUN pip install --no-cache-dir "agent-sandbox-server==0.4.0a2"

ENV HOME=/home/user WORKSPACE=/home/user/app GEMINI_MODEL=gemini-3.1-flash-lite
WORKDIR /home/user/app
COPY --chown=user:user commands.py byok.py relay.py process.py lifecycle.py upstream.json .
RUN chown user:user /home/user/app
USER user
EXPOSE 9000
