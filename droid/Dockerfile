FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV HOME=/home/user
ENV FACTORY_DROID_AUTO_UPDATE_ENABLED=false
ENV WORKSPACE=/home/user/app

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates git ripgrep \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /home/user/app \
    && chown -R user:user /home/user

# The platform image already provides Node >=20, required by this exact release.
# The base npm mirror lacks this release's native optional packages. The
# upstream fallback installer can otherwise leave bin/droid self-linked.
RUN npm install -g @factory/cli@0.241.1 --registry https://registry.npmjs.org --include=optional \
    && test "$(droid --version)" = "0.241.1" \
    && npm cache clean --force

COPY *.whl /tmp/
RUN if ls /tmp/*.whl 1>/dev/null 2>&1; then \
        pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl; \
    else \
        pip install --no-cache-dir "agent-sandbox-server @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/61c43e0be65a1f57aa09186d578e7b399e48429b.tar.gz#subdirectory=server-sdk"; \
    fi

WORKDIR /home/user/app
COPY --chown=user:user commands.py .
RUN chown user:user /home/user/app
USER user
EXPOSE 9000
