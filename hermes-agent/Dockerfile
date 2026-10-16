FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
# v0.22.1, immutable upstream commit; preserve its MIT license and uv.lock.
RUN pip install --no-cache-dir uv==0.12.3 \
    && mkdir -p /opt/hermes /opt/hermes-python \
    && curl -fsSL https://codeload.github.com/NousResearch/hermes-agent/tar.gz/297552a9d646119871391d202509822cd86330df \
       | tar -xz --strip-components=1 -C /opt/hermes \
    && UV_PYTHON_INSTALL_DIR=/opt/hermes-python uv python install 3.14.6 \
    && cd /opt/hermes \
    && UV_PYTHON_INSTALL_DIR=/opt/hermes-python uv sync --frozen --no-default-groups --python 3.14.6 \
    && .venv/bin/python scripts/write_install_stamp.py --output install-stamp.json \
       --commit 297552a9d646119871391d202509822cd86330df --base-version 0.22.1 --distance 0 \
       --source docker --distribution docker --update-mechanism external \
    && .venv/bin/hermes --version \
    && ln -s /opt/hermes/.venv/bin/hermes /usr/local/bin/hermes \
    && uv cache clean
COPY *.whl /tmp/
RUN if ls /tmp/*.whl 1>/dev/null 2>&1; then \
        pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl; \
    else \
        pip install --no-cache-dir "agent-sandbox-server @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/35da216a300f1e2e84254a1cf4b4a7ea98681505.tar.gz#subdirectory=server-sdk"; \
    fi
ENV HERMES_HOME=/home/user/.hermes
ENV WORKSPACE=/home/user/app
WORKDIR /home/user/app
COPY --chown=user:user commands.py .
USER user
EXPOSE 9000
