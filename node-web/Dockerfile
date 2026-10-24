FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>

ENV NODE_ENV=production
ENV PORT=3000
# The platform base supplies Node 20 and Python 3.13. No floating installers.
COPY *.whl /tmp/
RUN if ls /tmp/*.whl 1>/dev/null 2>&1; then \
        pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl; \
    else \
        pip install --no-cache-dir "agent-sandbox-server @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/e2cb27e24fde0a67112f82b8d44af463445a5d1a.tar.gz#subdirectory=server-sdk"; \
    fi

WORKDIR /home/user/app
COPY --chown=user:user index.js .
COPY --chown=user:user commands.py .
RUN chown user:user /home/user/app
USER user
EXPOSE 3000 9000
