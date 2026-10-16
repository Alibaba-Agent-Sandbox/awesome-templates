FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>

ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8
# Gemini CLI 0.64.0 supports the base image's Node.js >=20.
RUN npm install -g @google/gemini-cli@0.64.0 \
    && gemini --version \
    && npm cache clean --force

COPY *.whl /tmp/
RUN if ls /tmp/*.whl 1>/dev/null 2>&1; then \
        pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl; \
    else \
        pip install --no-cache-dir "agent-sandbox-server @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/35da216a300f1e2e84254a1cf4b4a7ea98681505.tar.gz#subdirectory=server-sdk"; \
    fi

ENV HOME=/home/user WORKSPACE=/home/user/app GEMINI_MODEL=gemini-3.1-flash-lite
WORKDIR /home/user/app
COPY --chown=user:user commands.py .
USER user
EXPOSE 9000
