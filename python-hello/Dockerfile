FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8

RUN pip install --no-cache-dir --index-url https://pypi.org/simple "agent-sandbox-server==0.4.0a6" \
    && pip install --no-cache-dir "pytest==8.4.2"

WORKDIR /home/user/app
COPY --chown=user:user commands.py .
RUN chown user:user /home/user/app
# Runtime defaults; credentials are supplied when creating an instance.
ENV LANG="C.UTF-8" \
    ABX_SERVER_TOKEN=""
USER user
EXPOSE 9000
