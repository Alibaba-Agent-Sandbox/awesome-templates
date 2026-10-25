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

COPY install_runtime.py assets.json /tmp/code-server-build/
RUN python3 /tmp/code-server-build/install_runtime.py --check-rootfs && rm -rf /tmp/code-server-build
ENV PATH="/opt/code-server/current/bin:${PATH}" WORKSPACE=/home/user/app
RUN pip install --no-cache-dir "agent-sandbox-server==0.4.0a2"

WORKDIR /home/user/app
COPY --chown=user:user commands.py .
RUN chown user:user /home/user/app
USER user
EXPOSE 9000 8443
