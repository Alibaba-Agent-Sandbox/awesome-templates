FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
# Alias flash-lite in @google/gemini-cli@0.64.0 resolves to this id.
ENV GEMINI_MODEL=gemini-3.1-flash-lite

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        git \
        gnupg \
        ripgrep \
    && rm -rf /var/lib/apt/lists/*

# Node.js 22, then the pinned Gemini CLI.
# npm view @google/gemini-cli version on 2026-10-14 resolved dist-tag latest to 0.64.0.
# The package bin name is gemini.
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g @google/gemini-cli@0.64.0 \
    && gemini --version

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
