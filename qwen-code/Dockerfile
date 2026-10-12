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

# Node.js 22 and the pinned qwen-code CLI. The DashScope key is injected at sandbox start.
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g @qwen-code/qwen-code@0.23.0

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir dashscope "openai>=1.0" httpx rich

# Pre-configure qwen-code for non-interactive, environment-based auth.
RUN mkdir -p /root/.qwen \
    && printf '%s\n' '{"security":{"auth":{"selectedType":"env-based"}},"core":{"nonInteractive":true}}' \
        > /root/.qwen/settings.json

# fc-deploy skill: scan the workdir, install deps, build, and start the service.
RUN mkdir -p /root/.qwen/skills/fc-deploy \
    && cat > /root/.qwen/skills/fc-deploy/SKILL.md << 'SKILL_EOF'
---
name: fc-deploy
description: 分析项目结构，安装依赖，构建，启动服务
---
# FC Sandbox 部署
1. 扫描 /app 确定项目类型和框架
2. 安装依赖 (pip install / npm install / go mod download)
3. 如需构建则执行构建命令
4. 启动服务并验证端口可达
5. 报告部署结果（JSON 格式：{"status", "url", "port", "logs"}）
SKILL_EOF

# Install easy-sandbox-server (the in-sandbox HTTP server, import easy_sandbox.server).
# ebx template deploy injects the wheel into the build context. Without a wheel, install from PyPI.
COPY *.whl /tmp/
RUN if ls /tmp/*.whl 1>/dev/null 2>&1; then \
        pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl; \
    else \
        pip install --no-cache-dir easy-sandbox-server; \
    fi

ENV WORKSPACE=/app
ENV OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
ENV OPENAI_MODEL=qwen3-coder-plus

WORKDIR /app
COPY commands.py .
EXPOSE 9000
CMD ["python3", "commands.py"]
