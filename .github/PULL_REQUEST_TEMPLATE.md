## Summary

<!-- What does this PR add or change? Which template(s)? Which test levels passed? -->

## Type of change

- [ ] New template
- [ ] Fix / update to an existing template
- [ ] Documentation
- [ ] Other

## Contributor checklist

- [ ] Follows [docs/template-spec.md](../docs/template-spec.md)
- [ ] Directory contains `template.yaml`, `Dockerfile`, `commands.py`, `e2e_test.py`, `README.md`, and `README.zh-CN.md`
- [ ] Dockerfile `FROM` is the Alibaba FC base image, `WORKDIR /home/user/app`, `USER user`, pinned versions, and no `CMD` / `ENTRYPOINT`
- [ ] `commands.py` imports `command` from `agent_sandbox.server`; `start()` is only under `if __name__ == "__main__"`
- [ ] `docs/design/<name>.md` filled from `docs/design/_TEMPLATE.md` (product templates)
- [ ] `awesome-templates.yaml` entry matches the directory name; `status` matches passed levels
- [ ] Explicit workflow/provides/default fields and evidence provenance agree; no author-written provider pass claims
- [ ] **No secrets** committed (API keys/tokens/passwords) — empty placeholders only
- [ ] `python3 scripts/check_template.py <name>` exits 0
- [ ] `python3 scripts/run_local_e2e.py` passes

## Notes for reviewers

<!-- Anything reviewers should pay attention to. -->
