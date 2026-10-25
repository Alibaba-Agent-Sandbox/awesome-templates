FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>

ENV NODE_ENV=production
ENV PORT=3000
# The platform base supplies Node 20 and Python 3.13. No floating installers.
RUN pip install --no-cache-dir --index-url https://pypi.org/simple "agent-sandbox-server==0.4.0a6"

WORKDIR /home/user/app
COPY --chown=user:user index.js .
COPY --chown=user:user commands.py .
RUN chown user:user /home/user/app
USER user
EXPOSE 3000 9000
