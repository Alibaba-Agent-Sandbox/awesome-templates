FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8

# Debian 13 FFmpeg and its matching ABI libraries. Preserve distribution notices.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ffmpeg=7:7.1.5-0+deb13u1 libavcodec61=7:7.1.5-0+deb13u1 \
       libavdevice61=7:7.1.5-0+deb13u1 libavfilter10=7:7.1.5-0+deb13u1 \
       libavformat61=7:7.1.5-0+deb13u1 libavutil59=7:7.1.5-0+deb13u1 \
       libpostproc58=7:7.1.5-0+deb13u1 libswresample5=7:7.1.5-0+deb13u1 \
       libswscale8=7:7.1.5-0+deb13u1 \
    && test "$(dpkg-query -W -f='${Version}' ffmpeg)" = '7:7.1.5-0+deb13u1' \
    && ffmpeg -version && ffprobe -version \
    && rm -rf /var/lib/apt/lists/*

COPY *.whl /tmp/
RUN if ls /tmp/*.whl 1>/dev/null 2>&1; then \
        pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl; \
    else \
        pip install --no-cache-dir "agent-sandbox-server @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/fd72d3210b85079d93dcf08e19bfded73643162b.tar.gz#subdirectory=server-sdk"; \
    fi

WORKDIR /home/user/app
COPY --chown=user:user commands.py .
RUN chown user:user /home/user/app
USER user
EXPOSE 9000
