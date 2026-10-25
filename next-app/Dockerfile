FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8 NEXT_TELEMETRY_DISABLED=1
COPY package.json package-lock.json /opt/next-app/
RUN npm ci --prefix /opt/next-app --ignore-scripts --no-audit --no-fund && npm cache clean --force
RUN pip install --no-cache-dir --index-url https://pypi.org/simple "agent-sandbox-server==0.4.0a2"

WORKDIR /home/user/app
COPY --chown=user:user commands.py lifecycle.py .
RUN chown user:user /home/user/app
USER user
EXPOSE 9000 3000 5173
