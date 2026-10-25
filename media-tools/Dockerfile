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

RUN pip install --no-cache-dir --index-url https://pypi.org/simple "agent-sandbox-server==0.4.0a4"

WORKDIR /home/user/app
COPY --chown=user:user commands.py .
RUN chown user:user /home/user/app
USER user
EXPOSE 9000
