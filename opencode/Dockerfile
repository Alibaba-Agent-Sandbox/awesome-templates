FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV HOME=/home/user
ENV OPENCODE_DISABLE_AUTOUPDATE=true
ENV OPENCODE_MODEL=dashscope/qwen3.8-flash
ENV OPENCODE_CONFIG=/home/user/app/opencode.json

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

RUN pip install --no-cache-dir --index-url https://pypi.org/simple "agent-sandbox-server==0.4.0a4"

WORKDIR /home/user/app
COPY --chown=user:user commands.py opencode.json ./
# Root installation/version probes can create native log/data state under HOME.
# Hand that state to the declared runtime user after all installer probes.
RUN chown -R user:user /home/user/app /home/user/.local /home/user/.config
USER user
EXPOSE 9000
EXPOSE 4096
