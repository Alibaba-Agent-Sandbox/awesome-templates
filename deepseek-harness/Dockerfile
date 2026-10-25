FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
RUN pip install --no-cache-dir httpx==0.28.1
RUN pip install --no-cache-dir "agent-sandbox-server==0.4.0a2"
ENV WORKSPACE=/home/user/app
WORKDIR /home/user/app
COPY --chown=user:user commands.py .
RUN chown user:user /home/user/app
USER user
EXPOSE 9000
