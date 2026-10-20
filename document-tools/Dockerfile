FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8

# Debian's code and data packages deliberately have different version strings.
RUN apt-get update \
    && apt-get install -y --no-install-recommends pandoc=3.1.11.1+ds-2 pandoc-data=3.1.11.1-3 \
       libreoffice-writer-nogui=4:25.2.3-2+deb13u8 \
       libreoffice-core-nogui=4:25.2.3-2+deb13u8 libreoffice-common=4:25.2.3-2+deb13u8 \
       fonts-dejavu-core=2.37-8 fonts-noto-cjk=1:20240730+repack1-1 \
    && test "$(dpkg-query -W -f='${Version}' pandoc)" = '3.1.11.1+ds-2' \
    && test "$(dpkg-query -W -f='${Version}' pandoc-data)" = '3.1.11.1-3' \
    && test "$(dpkg-query -W -f='${Version}' libreoffice-writer-nogui)" = '4:25.2.3-2+deb13u8' \
    && test "$(dpkg-query -W -f='${Version}' libreoffice-core-nogui)" = '4:25.2.3-2+deb13u8' \
    && /usr/lib/libreoffice/program/soffice.bin --headless --version \
    && pandoc --version \
    && rm -rf /var/lib/apt/lists/*

COPY *.whl /tmp/
RUN if ls /tmp/*.whl 1>/dev/null 2>&1; then \
        pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl; \
    else \
        pip install --no-cache-dir "agent-sandbox-server @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/e2cb27e24fde0a67112f82b8d44af463445a5d1a.tar.gz#subdirectory=server-sdk"; \
    fi

WORKDIR /home/user/app
COPY --chown=user:user commands.py .
RUN chown user:user /home/user/app
USER user
EXPOSE 9000
