FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV HOME=/home/user
ENV AMP_SETTINGS_FILE=/home/user/.config/amp/settings.json
ENV AMP_LOG_FILE=/home/user/.cache/amp/logs/cli.log
# npm view @ampcode/cli version on 2026-10-15. The linux-x64 optional package uses the same version.
ENV AMP_CLI_VERSION=0.0.1792022479-ge66e24

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        git \
        ripgrep \
    && rm -rf /var/lib/apt/lists/* \
    && node -v \
    && npm -v \
    && npm install -g "@ampcode/cli@${AMP_CLI_VERSION}" --registry https://registry.npmjs.org \
    && npm cache clean --force \
    && amp version \
    && command -v amp

# agent-sandbox-server is not on PyPI. Pin is python-sdk main 61c43e0 (PR #21).
# The echo keeps agent-sandbox-server==61c43e0be65a1f57aa09186d578e7b399e48429b in the build log.
RUN pip install --no-cache-dir "agent-sandbox-server @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/61c43e0be65a1f57aa09186d578e7b399e48429b.tar.gz#subdirectory=server-sdk" \
    && echo "agent-sandbox-server==61c43e0be65a1f57aa09186d578e7b399e48429b"

WORKDIR /home/user/app
COPY --chown=user:user commands.py .
RUN mkdir -p /home/user/.config/amp /home/user/.cache/amp/logs /home/user/app \
    && chown -R user:user /home/user/.config /home/user/.cache /home/user/app
USER user
EXPOSE 9000
