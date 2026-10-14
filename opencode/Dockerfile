FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
# OpenCode Zen free model documented at https://opencode.ai/docs/zen/ (id big-pickle).
ENV OPENCODE_MODEL=opencode/big-pickle
# Keep the npm pin. The CLI checks for updates unless this is set.
ENV OPENCODE_DISABLE_AUTOUPDATE=true

# python:3.12-slim already provides python3 and pip. Install them when the base image does not.
RUN if ! command -v python3 >/dev/null 2>&1 || ! command -v pip >/dev/null 2>&1; then \
        apt-get update && apt-get install -y --no-install-recommends python3 python3-pip \
        && rm -rf /var/lib/apt/lists/*; \
    fi

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
        git \
        gnupg \
        ripgrep \
    && rm -rf /var/lib/apt/lists/*

# Node.js 22 from the NodeSource setup script, then the pinned OpenCode CLI.
# npm view opencode-ai version on 2026-10-14 resolved dist-tag latest to 1.19.0.
# The package bin name is opencode. Do not copy the E2B or OpenSandbox Dockerfiles.
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g opencode-ai@1.19.0

# Install agent-sandbox-server (the in-sandbox HTTP server, import agent_sandbox.server).
# abx template deploy injects the wheel into the build context. Without a wheel, install from PyPI.
COPY *.whl /tmp/
RUN if ls /tmp/*.whl 1>/dev/null 2>&1; then \
        pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl; \
    else \
        pip install --no-cache-dir agent-sandbox-server; \
    fi

WORKDIR /app
COPY commands.py .
EXPOSE 9000
CMD ["python3", "commands.py"]
