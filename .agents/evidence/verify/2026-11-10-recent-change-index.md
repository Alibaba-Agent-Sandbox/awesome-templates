# Verification: recent awesome-templates change records

- Date: 2026-11-10
- Result: PASS (records-only checks; implementation gates remain separate)
- Scope: `.agents/README.md`, the recent-change process note and this evidence.
- Source revision inspected: `957cd1e3f52f7002cfe24a103653b855a7dd9747`.
- Mainline revision inspected: `e94ab308a74715982bb059b142518f7d6070c1c2`.
- Remote query timestamp: `2026-11-10T14:48:35.682193+00:00`.
- Environment: Linux, Git, Python 3; source and remote metadata inspection only.

## Commands and observations

- `git fetch origin --prune`: exit 0 in the owning source repository.
- `git status --short --branch`: the selected worktree was clean before this edit.
- `git log origin/main --first-parent --since=2026-11-05 -8`: inspected source history.
- `git rev-parse HEAD` and `git rev-parse origin/main`: revisions listed above.
- GitHub REST GET repository PR and Actions runs: remote metadata queried separately
  from any claim of executing tests locally. Authenticated REST supplied a consistent metadata snapshot.

## Prior source CI snapshot

[awesome-templates PR #305](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/305) was open, Draft and unmerged.

| Workflow | State | Result |
| --- | --- | --- |
| [e2e](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/42810877292) | completed | failure |
| [Template images (L1)](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/42810877278) | completed | failure |
| [Canonical Express review (explicit authorization only)](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/42810877233) | completed | success |

These results belong to the source revision above, before this records commit.
New commits require their own CI; a queued workflow is not a pass.

## Local records validation

- Scoped inline Markdown check below: exit 0; staged relative links resolved.
- One-off ADR/scope/privacy validation: PASS; seven ordered required sections,
  proposed lifecycle, 3 intended files, tracked index membership,
  no machine paths or credential-pattern matches. All 373
  relative links in the scoped documents resolved, including the existing README index.
- `git diff --cached --check -- .agents`: exit 0.
- Reviewed the staged `.agents` diff; no runtime/configuration/public article changes.
- `python3 scripts/check_docs.py`: exit 0, 234 public/design documents checked, 0 failures. New engineering records are also covered by the scoped check below.

Reproducible scoped link check, run from this repository after staging:

```bash
python3 - <<'PY'
from pathlib import Path
import re, subprocess
files = subprocess.check_output(
    ["git", "diff", "--cached", "--name-only"], text=True).splitlines()
for name in files:
    assert name.startswith(".agents/") and name.endswith(".md")
    path = Path(name)
    text = path.read_text()
    for target in re.findall(r"\[[^\]]*\]\(([^\s)]+)\)", text):
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("#"):
            continue
        assert (path.parent / target.split("#", 1)[0]).exists(), (name, target)
print("Scoped staged Markdown links: PASS")
PY
```


## Not verified and cleanup

No runtime, Docker, cloud, model, performance or new package-publication check was
run for this records-only change. Earlier acceptance retains its original scope.
No cloud resources were created, changed or deleted. Required implementation gates
remain with their existing PRs; this task does not declare those PRs complete.
