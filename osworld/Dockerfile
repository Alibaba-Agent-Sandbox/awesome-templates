FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/osworld-browser
ENV OSWORLD_RUNTIME_PYTHON=/opt/osworld/bin/python

# Debian 13 x86_64 desktop tools. Debian's transitive OS security packages remain
# repository-resolved; the browser revision and Python dependency graph are pinned.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       xvfb=2:21.1.16-1.3+deb13u4 openbox=3.6.1-12+b2 \
       python3-pyatspi=2.46.1-1 python3-gi=3.50.0-4+b1 \
       at-spi2-core=2.56.2-1+deb13u2 libatk-adaptor=2.56.2-1+deb13u2 \
       scrot=1.12.1-1 xauth=1:1.1.2-1.1 dbus=1.16.2-2 xclip=0.13-4 \
       python3-venv=3.13.5-1 python3-tk=3.13.5-1 fonts-dejavu-core=2.37-8 \
    && rm -rf /var/lib/apt/lists/* \
    && /usr/bin/python3 -m venv --system-site-packages /opt/osworld

COPY requirements.txt /opt/osworld/requirements.txt
RUN /opt/osworld/bin/pip install --no-cache-dir "pip==25.2" "setuptools==80.9.0" "wheel==0.45.1" "packaging==25.0" \
    && /opt/osworld/bin/pip install --no-cache-dir --no-build-isolation --require-hashes -r /opt/osworld/requirements.txt \
    && /opt/osworld/bin/python -m playwright install --with-deps chromium \
    && chmod -R a+rX /opt/osworld-browser

RUN pip install --no-cache-dir --index-url https://pypi.org/simple "agent-sandbox-server==0.4.0a4"

WORKDIR /home/user/app
COPY --chown=user:user upstream ./upstream
COPY --chown=user:user commands.py runtime.py .
RUN chown user:user /home/user/app
USER user
EXPOSE 9000
