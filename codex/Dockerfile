FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    CODEX_PIN=0.162.1 \
    CODEX_HOME=/home/user/.codex \
    WORKSPACE=/home/user/workspace \
    HOME=/home/user

# System bubblewrap is intentionally not installed. Codex prefers a `bwrap` on
# PATH over its bundled helper; a setuid-less distro bwrap in this container
# would shadow the helper that ships inside @openai/codex.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        git \
        jq \
        ripgrep \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g @openai/codex@0.162.1 \
    && npm cache clean --force

# Server source matches the common CI wheel source in scripts/server_sdk_pin.py.
# The PyPI name `agent-sandbox` is a different project, so the fallback installs
# that commit's server-sdk tree.
COPY *.whl /tmp/
RUN if ls /tmp/*.whl 1>/dev/null 2>&1; then \
        pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl; \
    else \
        pip install --no-cache-dir "agent-sandbox-server @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/e2cb27e24fde0a67112f82b8d44af463445a5d1a.tar.gz#subdirectory=server-sdk"; \
    fi

WORKDIR /home/user/app
COPY --chown=user:user commands.py AGENTS.md /home/user/app/
RUN mkdir -p /home/user/workspace /home/user/.codex \
    && cp /home/user/app/AGENTS.md /home/user/workspace/AGENTS.md \
    && git init /home/user/workspace \
    && git config --system --add safe.directory /home/user/workspace \
    && chown -R user:user /home/user/workspace /home/user/.codex /home/user/app
USER user
EXPOSE 9000
