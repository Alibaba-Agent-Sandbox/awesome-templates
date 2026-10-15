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

# agent-sandbox-server==0.3.0 is python-sdk 61c43e0 (includes PR #21).
# The PyPI name `agent-sandbox` is a different project, so the fallback installs
# that commit's server-sdk tree.
COPY *.whl /tmp/
RUN if ls /tmp/*.whl 1>/dev/null 2>&1; then \
        pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl; \
    else \
        pip install --no-cache-dir "agent-sandbox-server @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/61c43e0be65a1f57aa09186d578e7b399e48429b.tar.gz#subdirectory=server-sdk"; \
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
