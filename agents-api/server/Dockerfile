FROM python:3.13.8-slim-bookworm

RUN python -m pip install --no-cache-dir "agent-sandbox-client[managed-agents]==0.4.0a7" \
    && python -c "import agent_sandbox.managed_agents"

RUN useradd --create-home --uid 10001 app
USER app
WORKDIR /home/app
EXPOSE 9000
CMD ["python", "-m", "agent_sandbox.managed_agents", "gateway"]
