FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8

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

# Factory Droid CLI, pinned to the version the official installer publishes.
# https://app.factory.ai/cli sets VER=0.241.1.
# npm @factory/cli@0.241.1 (bin: droid) is the same release; npm builds disable auto-update.
# Docs: https://docs.factory.ai/droid-cli/cli-reference (npm install -g droid@<version>).
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g @factory/cli@0.241.1 \
    && droid --version

RUN pip install --no-cache-dir --upgrade pip

# Install agent-sandbox-server (the in-sandbox HTTP server, import agent_sandbox.server).
# abx template deploy injects the wheel into the build context. Without a wheel, install from PyPI.
COPY *.whl /tmp/
RUN if ls /tmp/*.whl 1>/dev/null 2>&1; then \
        pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl; \
    else \
        pip install --no-cache-dir agent-sandbox-server; \
    fi

# npm builds already disable auto-update. Keep that behavior if the binary is invoked directly.
ENV FACTORY_DROID_AUTO_UPDATE_ENABLED=false
ENV WORKSPACE=/app

WORKDIR /app
COPY commands.py .
EXPOSE 9000
CMD ["python3", "commands.py"]
