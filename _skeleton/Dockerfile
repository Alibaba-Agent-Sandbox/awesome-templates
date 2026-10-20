FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8

# abx template deploy substitutes <region> and <tag> (default cn-hangzhou and v0.0.49).
# Layer order: heavy tool installs go in the early RUN below. commands.py is
# copied last, so a command edit does not rebuild or re-push the tool layer.
# pip --no-cache-dir keeps that layer from storing a download cache.
# Example (pin the package version):
#   RUN apt-get update && apt-get install -y --no-install-recommends git=<version> \
#       && rm -rf /var/lib/apt/lists/*

# Allowed server pins (docs/template-spec.md): agent-sandbox-server==X.Y.Z, or the
# python-sdk archive URL with a 40-hex commit. 0.3.0 is not on PyPI. This archive
# is python-sdk main 35da216 (includes 61c43e0 / PR #21). A wheel in the build
# context wins when abx template deploy injects one.
COPY *.whl /tmp/
RUN if ls /tmp/*.whl 1>/dev/null 2>&1; then \
        pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl; \
    else \
        pip install --no-cache-dir "agent-sandbox-server @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/35da216a300f1e2e84254a1cf4b4a7ea98681505.tar.gz#subdirectory=server-sdk"; \
    fi

WORKDIR /home/user/app
COPY --chown=user:user commands.py .
RUN chown user:user /home/user/app
USER user
EXPOSE 9000
