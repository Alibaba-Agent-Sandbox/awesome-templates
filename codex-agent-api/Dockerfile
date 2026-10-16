FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    CODEX_HOME=/home/user/.codex \
    WORKSPACE=/home/user/workspace \
    AGENT_MAX_SESSIONS=20 \
    AGENT_SESSION_TTL=1800 \
    CODEX_SANDBOX=workspace-write

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates git ripgrep \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g @openai/codex@0.162.1 \
    && npm cache clean --force

COPY *.whl /tmp/
RUN if ls /tmp/*.whl 1>/dev/null 2>&1; then \
        pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl; \
    else \
        pip install --no-cache-dir "agent-sandbox-server @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/e2cb27e24fde0a67112f82b8d44af463445a5d1a.tar.gz#subdirectory=server-sdk"; \
    fi

WORKDIR /home/user/app
COPY --chown=user:user commands.py .
RUN mkdir -p /home/user/workspace /home/user/.codex \
    && chown -R user:user /home/user/app /home/user/workspace /home/user/.codex
USER user
EXPOSE 9000
