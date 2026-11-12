FROM python:3.13.8-slim-bookworm

RUN python -m pip install --no-cache-dir "agent-sandbox-client[managed-agents] @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/b988d2a76057b6202d836ec329cc0bd90a572b26.tar.gz#subdirectory=client-sdk&sha256=abefcb1f16d7c87089d9d560d4f8ebd5787a140351553b84f970a171fdd18f68" \
    && python -c "from agent_sandbox.managed_agents.models import ManagedConfig; assert {'instance', 'instance_env_names'} <= set(ManagedConfig.__dataclass_fields__)"

RUN useradd --create-home --uid 10001 app
USER app
WORKDIR /home/app
EXPOSE 9000
CMD ["python", "-m", "agent_sandbox.managed_agents", "gateway"]
