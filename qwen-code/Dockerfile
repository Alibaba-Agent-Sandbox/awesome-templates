FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>

ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8
# Qwen Code 0.23.0 requires Node >=22; do not silently use an older base runtime.
RUN if ! command -v node >/dev/null 2>&1 || ! node -e "process.exit(Number(process.versions.node.split('.')[0]) >= 22 ? 0 : 1)"; then \
        curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
        && apt-get install -y --no-install-recommends nodejs \
        && rm -rf /var/lib/apt/lists/*; \
    fi \
    && npm install -g @qwen-code/qwen-code@0.23.0 \
    && qwen --version

COPY *.whl /tmp/
RUN if ls /tmp/*.whl 1>/dev/null 2>&1; then \
        pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl; \
    else \
        pip install --no-cache-dir "agent-sandbox-server @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/35da216a300f1e2e84254a1cf4b4a7ea98681505.tar.gz#subdirectory=server-sdk"; \
    fi

ENV HOME=/home/user WORKSPACE=/home/user/app
ENV OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
ENV OPENAI_MODEL=qwen3-coder-plus
WORKDIR /home/user/app
COPY --chown=user:user commands.py .
USER user
EXPOSE 9000
