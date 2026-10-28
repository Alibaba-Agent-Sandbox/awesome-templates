# Verification: awesome-templates README audience review

- Date: 2026-10-28
- Result: PASS — scoped local documentation verification. Remote checks and merge are reported separately on the PR.
- Base revision: `d2112dfc5fc93be8394ff787ccc5b83d11c37c72`.
- Scope: `README.md`, `README.zh-CN.md`, `docs/using-templates.md`, `docs/using-templates.zh-CN.md`; repository-owned note and this evidence.
- Environment: Linux, Node.js 22.22.2, system Python 3.13.13; SDK/server and checker environment Python 3.11.15.

## What was reviewed

The root mixed both languages and required readers to choose/save an application token manually. Its long alphabetical status table described implementation pins rather than helping readers find a task. The linked shared guide also required a manual token for CLI-only use.

Provide separate language READMEs, one complete launch/run/kill task and the same complete source catalog grouped by user task. Separate provider-managed runtimes. Explain automatic default application authentication, preserve external-client custom-token instructions in the shared bilingual guide, and link build prerequisites and retained-resource cleanup. No template implementation, manifest, catalog identity or qualification is changed.

## Validation

`python "$README_AUDIT"` passed for 7 changed Markdown files, with zero failures. This temporary audit used the existing template repository's Markdown-target/heading parser at its checked-out base revision and a task wrapper (SHA-256 `fe8c34fd4ef2474ca7dfcfcc94d2a055e9ead01a92fe2695446cfe08341df7e6`). It checks changed local targets/fragments, incoming active README heading links, one H1 and reciprocal language links in each root README, balanced fences and Python snippet syntax. `README_AUDIT` denotes that temporary wrapper; no machine-local path is part of the repository. It does not validate cloud runtime behavior.

`git -c core.filemode=false diff --check HEAD` passed. The filesystem exposes executable bits on unchanged checkout files; ignoring those bits for task-local Git commands avoided including unrelated mode changes. The staged change was reviewed for prose-only scope, translation equivalence, current command/API names and preserved license links. Package registry checks on 2026-10-28 found CLI 0.5.8 and Python client 0.4.0a6; the Node SDK public npm metadata endpoint returned HTTP 404. No new package publication is claimed.

## Limits and cleanup

Documentation changes only. No provider API calls, sandboxes, templates, cloud keys, model calls, deployments or package releases were created by local verification. Existing historical receipts remain unchanged. CI and existing main-branch publication workflows retain their own scope.

## Repository checks

- `python scripts/check_docs.py`: PASS: 225 documents, 0 failures.
- `python scripts/check_template.py --all`: BLOCKED initially: system Python lacked PyYAML.
- `python scripts/check_template.py --all (Python environment with checker dependencies)`: PASS: 0 claimed-spec failures.

## Reviewed public-file identity

| File | SHA-256 |
| --- | --- |
| `README.md` | `8950d095e2e36b4b34f319858ab78bcf2ca4572c18f5c9a373f436853327cb42` |
| `README.zh-CN.md` | `003ccd9d0887dc6cdd45d570519f946666e6fd989f7583d80a140089a62bff11` |
| `docs/using-templates.md` | `030f82f89dd2b226355196c494e6eaab7d835fb3816ff79145ec247d42768c38` |
| `docs/using-templates.zh-CN.md` | `dbe825ef2c08e5fc3a7b541d0844da64afb6ec7136c569369f178f34ba398fd4` |

## Editorial follow-up

Refined the agent category and descriptions to distinguish the OpenClaw gateway, Hermes assistant, DeepAgents tools and the bounded mini-swe-agent Flask task. The template implementations and acceptance inputs remain unchanged.
