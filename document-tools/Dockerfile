FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8

# Resolve the reviewed engine packages from signed, dated Debian repositories.
RUN printf '%s\n' \
      'Types: deb' \
      'URIs: http://snapshot.debian.org/archive/debian/20261112T000000Z' \
      'Suites: trixie trixie-updates' \
      'Components: main' \
      'Signed-By: /usr/share/keyrings/debian-archive-keyring.pgp' \
      'Check-Valid-Until: no' \
      '' \
      'Types: deb' \
      'URIs: http://snapshot.debian.org/archive/debian-security/20261112T000000Z' \
      'Suites: trixie-security' \
      'Components: main' \
      'Signed-By: /usr/share/keyrings/debian-archive-keyring.pgp' \
      'Check-Valid-Until: no' > /etc/apt/sources.list.d/debian.sources

# Debian's code and data packages deliberately have different version strings.
RUN apt-get update \
    && apt-get install -y --no-install-recommends pandoc=3.1.11.1+ds-2 pandoc-data=3.1.11.1-3 \
       libreoffice-writer-nogui=4:25.2.3-2+deb13u9 \
       libreoffice-core-nogui=4:25.2.3-2+deb13u9 libreoffice-common=4:25.2.3-2+deb13u9 \
       fonts-dejavu-core=2.37-8 fonts-noto-cjk=1:20240730+repack1-1 \
    && test "$(dpkg-query -W -f='${Version}' pandoc)" = '3.1.11.1+ds-2' \
    && test "$(dpkg-query -W -f='${Version}' pandoc-data)" = '3.1.11.1-3' \
    && test "$(dpkg-query -W -f='${Version}' libreoffice-writer-nogui)" = '4:25.2.3-2+deb13u9' \
    && test "$(dpkg-query -W -f='${Version}' libreoffice-core-nogui)" = '4:25.2.3-2+deb13u9' \
    && /usr/lib/libreoffice/program/soffice.bin --headless --version \
    && pandoc --version \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --index-url https://pypi.org/simple "agent-sandbox-server==0.4.0a6"

WORKDIR /home/user/app
COPY --chown=user:user commands.py .
RUN chown user:user /home/user/app
USER user
EXPOSE 9000
