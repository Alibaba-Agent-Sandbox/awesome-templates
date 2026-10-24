# Source application quick-start verification — 2026-10-24

Status: PARTIAL — local checks pass; candidate cloud repetition and remote CI pending.

## Inputs and scope

Base: `ba17fbd32da188a2e4452f5946fa72135fc41c8e`. Documentation-only changes to
46 source-template README pairs and `_skeleton`; no source runtime, Dockerfile,
manifest, model dependency or historical receipt changes. The shared guide already
uses public CLI0.4.16 and Python client0.3.1a5. This record does not requalify the
original 92-case matrix under new README/source digests.

Before editing, a scoped scan of active quick-start text found create examples in
46/46 source templates, implicit `sb.run` in 38/46, URL-only `network.get_url` in
27/46, detached create environment injection in 8/46, and stale Stack
requalification text in 13/46. These are matched documentation patterns, not 46
independent runtime failures. `_skeleton` shared the obsolete examples.

## Local checks

- PASS: `python scripts/check_docs.py`: 222 documents, zero link/fragment failures.
- PASS: `python scripts/check_template.py --all`: zero claimed spec failures.
- PASS: 98 Python fenced blocks parsed with `ast.parse`; snippets using `await`
  retain their documented enclosing async context. This is syntax, not execution.
- PASS: all 47 bilingual entries retain an actual manifest smoke command. An
  active-text scan before Verified finds no `sb.run`, `Sandbox.create`, `abx create`
  or URL-only `network.get_url` examples.
- PASS: `python -m pytest -q qwen-code/test_commands.py`: 11 passed in the existing
  SDK development environment. Initial execution in the checker-only environment
  FAILED collection because `agent_sandbox` was absent; the correctly provisioned
  environment rerun passed. No model or cloud was called by these unit tests.
- PASS: `git diff --check`; all current changed files are README pairs.

## API review

Compared published CLI source/help: positional upload/download, `template launch`
with workflow and sandbox timeout, named command discovery/run and owned kill.
CLI0.4.16 `requestApplication` defaults to 30 seconds and `runCommand` does not
forward a configurable deadline: long Qwen calls are documented through Python
and HTTP with 330-second waits, separately from 300-second task deadlines.
Qwen manifest empty secret values inherit the launching shell; nonempty defaults
win over shell values, so endpoint/workspace changes explicitly edit the manifest
before launch. No late export is claimed to reconfigure an application.

## Remaining gates

Actual Qwen keyless Express repeat, exact refs/installed versions, independent
owned cleanup, remote CI and review remain pending. No new real-model pass,
OpenSandbox Qwen pass, all-template end-to-end pass or public deployment of these
docs is claimed here.
