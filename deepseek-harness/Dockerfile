FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
RUN pip install --no-cache-dir httpx==0.28.1
RUN pip install --no-cache-dir --index-url https://pypi.org/simple "agent-sandbox-server==0.4.0a6"
ENV WORKSPACE=/home/user/app
WORKDIR /home/user/app
COPY --chown=user:user commands.py .
RUN chown user:user /home/user/app
# Runtime defaults; credentials are supplied when creating an instance.
ENV WORKSPACE="/home/user/app" \
    ABX_SERVER_TOKEN="" \
    DEEPSEEK_API_KEY="" \
    OPENAI_API_KEY="" \
    DEEPSEEK_BASE_URL="" \
    DEEPSEEK_MODEL=""
USER user
EXPOSE 9000
