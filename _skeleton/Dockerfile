FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8

# abx template deploy substitutes <region> and <tag> (default cn-hangzhou and v0.0.49)
# and injects an agent-sandbox-server wheel when one is available.
COPY *.whl /tmp/
RUN if ls /tmp/*.whl 1>/dev/null 2>&1; then \
        pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl; \
    else \
        pip install --no-cache-dir "agent-sandbox-server==0.3.0"; \
    fi

WORKDIR /home/user/app
COPY --chown=user:user commands.py .
USER user
EXPOSE 9000
