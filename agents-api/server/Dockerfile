FROM python:3.13.8-slim-bookworm

RUN python -m pip install --no-cache-dir "agent-sandbox-client[managed-agents] @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/c550cf53a9eb0c3c9899d0336b924633eb9b0988.tar.gz#subdirectory=client-sdk&sha256=e5c8c5b1d4deef7a49f720a4e42cfca709652551fc379e1f7b1f7dec00e1afe9" \
    && python -c "from agent_sandbox.managed_agents.models import ManagedConfig; assert {'instance', 'instance_env_names'} <= set(ManagedConfig.__dataclass_fields__)"

RUN useradd --create-home --uid 10001 app
USER app
WORKDIR /home/app
EXPOSE 9000
CMD ["python", "-m", "agent_sandbox.managed_agents", "gateway"]
