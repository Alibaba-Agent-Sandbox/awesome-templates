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
        jq \
        ripgrep \
        wget \
    && rm -rf /var/lib/apt/lists/*

# Node.js 22 plus the Codex CLI that backs the Agents API routes.
# The API key is injected at sandbox start and is not written into the image.
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g @openai/codex

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir "openai>=1.0" rich httpx

# Install easy-sandbox-server (the in-sandbox HTTP server, import easy_sandbox.server).
# ebx template deploy injects the wheel into the build context. Without a wheel, install from PyPI.
COPY *.whl /tmp/
RUN if ls /tmp/*.whl 1>/dev/null 2>&1; then \
        pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl; \
    else \
        pip install --no-cache-dir easy-sandbox-server; \
    fi

ENV CODEX_MODEL=codex-mini
ENV CODEX_SANDBOX_MODE=true
ENV AGENT_MAX_SESSIONS=20
ENV AGENT_SESSION_TTL=1800
ENV WORKSPACE=/app

WORKDIR /app
COPY commands.py .
EXPOSE 9000
CMD ["python3", "commands.py"]
