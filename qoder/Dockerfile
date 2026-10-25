FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8

# The platform base supplies Node.js >=20. Use the versioned npm compatibility
# channel rather than the upstream native installer, which tracks latest.
RUN npm install -g @qoder-ai/qodercli@1.1.72 \
    && qodercli --version \
    && npm cache clean --force

RUN pip install --no-cache-dir "agent-sandbox-server==0.4.0a2"

ENV WORKSPACE=/home/user/app
WORKDIR /home/user/app
COPY --chown=user:user commands.py .
RUN chown user:user /home/user/app
USER user
EXPOSE 9000
