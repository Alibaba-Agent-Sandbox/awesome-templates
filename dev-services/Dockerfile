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
ENV WORKSPACE=/home/user/app DEV_SERVICES_POSTGRES_PORT=5432 DEV_SERVICES_REDIS_PORT=16379
RUN pip install --no-cache-dir --index-url https://pypi.org/simple "agent-sandbox-server==0.4.0a2"

WORKDIR /home/user/app
COPY --chown=user:user commands.py lifecycle.py .
RUN chown user:user /home/user/app
USER user
EXPOSE 9000 5432 16379
