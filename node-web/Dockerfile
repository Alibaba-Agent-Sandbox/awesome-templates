FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8

# python:3.12-slim already provides python3 and pip. Install them when the base image does not.
RUN if ! command -v python3 >/dev/null 2>&1 || ! command -v pip >/dev/null 2>&1; then \
        apt-get update && apt-get install -y --no-install-recommends python3 python3-pip \
        && rm -rf /var/lib/apt/lists/*; \
    fi

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        git \
        gnupg \
        jq \
        wget \
    && rm -rf /var/lib/apt/lists/*

# Node.js 20 is this template's web runtime (Express, Fastify, and similar).
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g --force yarn nodemon pm2

# Install agent-sandbox-server (the in-sandbox HTTP server, import agent_sandbox.server).
# abx template deploy injects the wheel into the build context. Without a wheel, install from PyPI.
COPY *.whl /tmp/
RUN if ls /tmp/*.whl 1>/dev/null 2>&1; then \
        pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl; \
    else \
        pip install --no-cache-dir agent-sandbox-server; \
    fi

ENV NODE_ENV=production
ENV PORT=3000

WORKDIR /app
COPY commands.py .

EXPOSE 3000
EXPOSE 9000
CMD ["python3", "commands.py"]
