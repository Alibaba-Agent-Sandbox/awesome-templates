FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8

# git, curl, ca-certificates, ripgrep. gnupg is required by the NodeSource setup script.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        git \
        gnupg \
        ripgrep \
    && rm -rf /var/lib/apt/lists/*

# Node.js 22 via NodeSource, then a pinned Amp CLI. AMP_API_KEY is injected at sandbox start.
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g @ampcode/cli@0.0.1791964847-g13f24a

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
