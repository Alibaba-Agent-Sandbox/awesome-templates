FROM python:3.13.8-slim-bookworm

# Requires the paired runtime release; do not substitute an older published runtime.
RUN python -m pip install --no-cache-dir "agent-sandbox-client[managed-agents]==0.4.0a8"

RUN useradd --create-home --uid 10001 app
COPY --chown=app:app server/bootstrap.py /home/app/bootstrap.py
COPY --chown=app:app server/harness.json /home/app/harness.json
USER app
WORKDIR /home/app
EXPOSE 9000
ENTRYPOINT ["python", "/home/app/bootstrap.py"]
CMD ["gateway"]
