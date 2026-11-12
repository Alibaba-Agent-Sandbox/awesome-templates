FROM python:3.13.8-slim-bookworm

RUN python -m pip install --no-cache-dir "agent-sandbox-client[managed-agents] @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/1079841307f1f63253ae68fdda6e6d2d1e77e851.tar.gz#subdirectory=client-sdk&sha256=a7dfffac2eba7a8ee3d5620d231c5abf3f767ca655194b7329341389faf83485" \
    && python -c "from agent_sandbox.managed_agents.models import ManagedConfig; assert {'instance', 'instance_env_names'} <= set(ManagedConfig.__dataclass_fields__)"

RUN useradd --create-home --uid 10001 app
USER app
WORKDIR /home/app
EXPOSE 9000
CMD ["python", "-m", "agent_sandbox.managed_agents", "gateway"]
