## Summary

<!-- What does this PR add or change? Which template(s)? Which commands and provider entry points were tested? -->

## Type of change

- [ ] New template
- [ ] Fix / update to an existing template
- [ ] Documentation
- [ ] Other

## Contributor checklist

- [ ] Follows [docs/template-spec.md](../docs/template-spec.md)
- [ ] Directory contains `template.yaml`, `Dockerfile`, `commands.py`, `e2e_test.py`, `README.md`, and `README.zh-CN.md`
- [ ] Default Express Dockerfile retains its platform base and non-root contract; additional build profiles are explicit, pinned, non-root, selected by name, and preserve the original recipe
- [ ] `commands.py` imports `command` from `agent_sandbox.server`; `start()` is only under `if __name__ == "__main__"`
- [ ] `docs/design/<name>.md` filled from `docs/design/_TEMPLATE.md` (product templates)
- [ ] `awesome-templates.yaml` entry matches the directory name; `status` reflects maintenance ownership; exact template/provider results are recorded separately
- [ ] Startup, provided services and evidence provenance agree; no author-written provider pass claims
- [ ] **No secrets** committed (API keys/tokens/passwords) — empty placeholders only
- [ ] `python3 scripts/check_template.py <name>` exits 0
- [ ] `python3 scripts/run_local_e2e.py` passes

## Notes for reviewers

<!-- Anything reviewers should pay attention to. -->
