FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8
# Prevent package installation from creating/starting a root-owned default cluster.
RUN mkdir -p /etc/postgresql-common \
    && printf 'create_main_cluster = false\n' > /etc/postgresql-common/createcluster.conf \
    && printf '#!/bin/sh\nexit 101\n' > /usr/sbin/policy-rc.d \
    && chmod 755 /usr/sbin/policy-rc.d \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
       postgresql-17=17.11-0+deb13u1 postgresql-client-17=17.11-0+deb13u1 \
       libpq5=17.11-0+deb13u1 redis-server=5:8.0.2-3+deb13u3 redis-tools=5:8.0.2-3+deb13u3 \
    && dpkg-query -W postgresql-17 postgresql-client-17 libpq5 redis-server redis-tools \
    && rm -rf /var/lib/apt/lists/*
ENV WORKSPACE=/home/user/app
COPY *.whl /tmp/
RUN if ls /tmp/*.whl 1>/dev/null 2>&1; then \
        pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl; \
    else \
        pip install --no-cache-dir "agent-sandbox-server @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/e2cb27e24fde0a67112f82b8d44af463445a5d1a.tar.gz#subdirectory=server-sdk"; \
    fi

WORKDIR /home/user/app
COPY --chown=user:user commands.py lifecycle.py .
RUN chown user:user /home/user/app
USER user
EXPOSE 9000 5432 6379
