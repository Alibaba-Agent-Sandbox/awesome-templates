## Summary

<!-- What does this PR add or change? Which template(s)? -->

## Type of change

- [ ] New template
- [ ] Fix / update to an existing template
- [ ] Documentation
- [ ] Other

## Contributor checklist

- [ ] Template directory contains `template.yaml`, `Dockerfile`, `commands.py`, `e2e_test.py`, and `README.md`
- [ ] Dockerfile is `FROM python:3.12-slim`, `WORKDIR /app`, `CMD ["python3", "commands.py"]`, and installs `easy-sandbox-server`
- [ ] `awesome-templates.yaml` index updated (name / description / repo / path / tags / author / capabilities / status)
- [ ] Directory name == `template.yaml` `name` == index `path`
- [ ] Local install passes: `ebx template install ./<name> --registry-type local`
- [ ] `commands.py` imports cleanly; only required capability groups enabled
- [ ] Capabilities in `template.yaml` match the groups enabled in `commands.py`
- [ ] **No secrets** committed (API keys/tokens/passwords) — placeholders only
- [ ] No build junk (`__pycache__/`, `*.pyc`, `.DS_Store`)
- [ ] Uses current naming: **Easy Sandbox / ebx / easy-sandbox / easy-sandbox-server / easy_sandbox / Easy-Sandbox**
- [ ] `python3 scripts/run_local_e2e.py` passes (or skips this template with an explicit reason)

## Notes for reviewers

<!-- Anything reviewers should pay attention to. -->
