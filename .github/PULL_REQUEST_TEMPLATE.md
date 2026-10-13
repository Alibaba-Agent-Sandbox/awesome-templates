## Summary

<!-- What does this PR add or change? Which template(s)? -->

## Type of change

- [ ] New template
- [ ] Fix / update to an existing template
- [ ] Documentation
- [ ] Other

## Contributor checklist

- [ ] Template directory contains `template.yaml`, `Dockerfile`, `commands.py`, `e2e_test.py`, and `README.md`
- [ ] Dockerfile is `FROM python:3.12-slim`, `WORKDIR /app`, `CMD ["python3", "commands.py"]`, and installs `agent-sandbox-server`
- [ ] `awesome-templates.yaml` index updated (name / description / repo / path / tags / author / capabilities / status)
- [ ] Directory name == `template.yaml` `name` == index `path`
- [ ] Local install passes: `abx template install ./<name> --registry-type local`
- [ ] Named commands are registered in `commands.py` with `@command`; `template.yaml` has no command map
- [ ] `template.yaml` `server:` (if present) is an endpoint policy; a group is only a name for a batch of endpoints (`groups` takes a list or a map)
- [ ] **No secrets** committed (API keys/tokens/passwords) — placeholders only
- [ ] No build junk (`__pycache__/`, `*.pyc`, `.DS_Store`)
- [ ] Uses current naming: **Agent Sandbox / abx / agent-sandbox / agent-sandbox-server / agent_sandbox / alibaba-agent-sandbox**
- [ ] `python3 scripts/run_local_e2e.py` passes for every template

## Notes for reviewers

<!-- Anything reviewers should pay attention to. -->
