FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV HOME=/home/user
ENV OPENCODE_DISABLE_AUTOUPDATE=true
ENV OPENCODE_MODEL=dashscope/qwen3.8-flash
ENV OPENCODE_CONFIG=/home/user/app/opencode.json

# Spec fallback pin agent-sandbox-server==0.3.0 is not what this image runs.
# python-sdk main 61c43e0be65a1f57aa09186d578e7b399e48429b includes PR #21.
# abx template deploy substitutes <region> and <tag> and may inject a wheel.

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        git \
        ripgrep \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /home/user/app /home/user/.config /home/user/.local \
    && chown -R user:user /home/user

# npm view opencode-ai version on 2026-10-15 resolved dist-tag latest to 1.19.0.
# The package bin name is opencode. Node.js 20 is already in the base image.
# npm also unpacks the baseline binary and a cache under $HOME. Drop both in
# this layer. The copied bin is the AVX2 build, which is what `opencode --version` ran.
RUN node --version && npm --version \
    && npm install -g opencode-ai@1.19.0 \
    && opencode --version \
    && test "$(opencode --version)" = "1.19.0" \
    && rm -rf \
        /usr/local/lib/node_modules/opencode-ai/node_modules/opencode-linux-x64-baseline \
        /usr/local/lib/node_modules/opencode-ai/node_modules/opencode-linux-x64-musl \
        /usr/local/lib/node_modules/opencode-ai/node_modules/opencode-linux-x64-baseline-musl \
        /root/.npm \
        /home/user/.npm

COPY *.whl /tmp/
RUN if ls /tmp/*.whl 1>/dev/null 2>&1; then \
        pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl; \
    else \
        pip install --no-cache-dir "agent-sandbox-server @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/61c43e0be65a1f57aa09186d578e7b399e48429b.tar.gz#subdirectory=server-sdk"; \
    fi

WORKDIR /home/user/app
COPY --chown=user:user commands.py opencode.json ./
USER user
EXPOSE 9000
EXPOSE 4096
