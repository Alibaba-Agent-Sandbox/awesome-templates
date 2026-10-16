FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8

# The platform base supplies Node.js >=20. Use the versioned npm compatibility
# channel rather than the upstream native installer, which tracks latest.
RUN npm install -g @qoder-ai/qodercli@1.1.72 \
    && qodercli --version \
    && npm cache clean --force

COPY *.whl /tmp/
RUN if ls /tmp/*.whl 1>/dev/null 2>&1; then \
        pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl; \
    else \
        pip install --no-cache-dir "agent-sandbox-server @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/35da216a300f1e2e84254a1cf4b4a7ea98681505.tar.gz#subdirectory=server-sdk"; \
    fi

ENV WORKSPACE=/home/user/app
WORKDIR /home/user/app
COPY --chown=user:user commands.py .
USER user
EXPOSE 9000
