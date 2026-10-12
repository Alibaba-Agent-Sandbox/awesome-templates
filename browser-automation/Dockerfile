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
        jq \
        wget \
        xvfb \
    && rm -rf /var/lib/apt/lists/*

# Playwright + Chromium for the browser commands. Keys are not written into the image.
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
        "playwright>=1.40.0" \
        beautifulsoup4 \
        lxml \
        httpx \
        Pillow \
    && python3 -m playwright install --with-deps chromium

# Install easy-sandbox-server (the in-sandbox HTTP server, import easy_sandbox.server).
# ebx template deploy injects the wheel into the build context. Without a wheel, install from PyPI.
COPY *.whl /tmp/
RUN if ls /tmp/*.whl 1>/dev/null 2>&1; then \
        pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl; \
    else \
        pip install --no-cache-dir easy-sandbox-server; \
    fi

ENV DISPLAY=:99
ENV PLAYWRIGHT_BROWSERS_PATH=/root/.cache/ms-playwright

WORKDIR /app
COPY commands.py .
EXPOSE 9000
CMD ["python3", "commands.py"]
