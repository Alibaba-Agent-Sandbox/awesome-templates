FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8

# Source preparation substitutes <region> and <tag> before building.
# Layer order: heavy tool installs go in the early RUN below. commands.py is
# copied last, so a command edit does not rebuild or re-push the tool layer.
# pip --no-cache-dir keeps that layer from storing a download cache.
# Example (pin the package version):
#   RUN apt-get update && apt-get install -y --no-install-recommends git=<version> \
#       && rm -rf /var/lib/apt/lists/*

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev libstdc++6 zlib1g && rm -rf /var/lib/apt/lists/*
COPY install_toolchains.py toolchains.json /tmp/toolchain-build/
RUN python3 /tmp/toolchain-build/install_toolchains.py && rm -rf /tmp/toolchain-build
ENV PATH="/opt/toolchains/go/bin:/opt/toolchains/rust/bin:/opt/toolchains/java/bin:${PATH}" JAVA_HOME=/opt/toolchains/java GOTOOLCHAIN=local

RUN pip install --no-cache-dir --index-url https://pypi.org/simple "agent-sandbox-server==0.4.0a6"

WORKDIR /home/user/app
COPY --chown=user:user commands.py .
RUN chown user:user /home/user/app
# Runtime defaults; credentials are supplied when creating an instance.
ENV ABX_SERVER_TOKEN=""
USER user
EXPOSE 9000
