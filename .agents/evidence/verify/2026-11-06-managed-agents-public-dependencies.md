# Managed Agents public dependency transition

Date: 2026-11-06
Result: PARTIAL

The existing template branch already contains accepted contract main
31fe653c2940d8681b9549be3f570977152847a7 as an ancestor. The actual merge-base
ancestor check returned0; no rewrite or duplicate contract merge was performed.

The producer verified all four actual PyPI0.4.0a7 files against CI source906.
Both Dockerfiles now pin the published a7 packages and retain public pip installs;
there is no local wheel COPY or source installation fallback. The earlier a6
dependency caveat is replaced with supported runtime prerequisites. Bilingual
quickstarts specify Node20+, npm CLI0.5.9 and httpx0.28.1 in `.abx/venv`, already
excluded from the Docker context. Business HTTP clients need no management SDK.

At this edit npm0.5.9 publication and exact public-recipe cloud acceptance remain
pending. The PR must not merge or claim that acceptance before those gates pass.
The manifest remains0.1.2/Beta. Its normal FC source-wheel run used earlier cd43
CI wheels and is not relabeled as the newly published package identity.

Actual local checks:

- `python scripts/check_template.py agents-api`: conformant, exit0.
- `python scripts/check_docs.py`:232 documents,0 link failures, exit0.
- The first smoke test invocation failed before collection because the checker
  venv had no pytest. Installed the repository CI's exact pytest9.1.1 plus the
  documented httpx0.28.1 in that existing verification venv, then
  `python -m pytest agents-api/test_smoke.py -q`:7 passed in14.98s, exit0.
- Scoped `git -c core.fileMode=false diff --check`: exit0.

Actual peer review and the new-head image/public-cloud results remain separate.
No cloud resource was created or mutated by this dependency/document change.

The CLI/deployment reviewer independently read all four recipe/README changes
and accepted this scope. The Server base remains python3.13.8-slim; image probes
must derive installed distribution paths instead of assuming Python3.12.
Commit/push starts latest-head CI; it does not grant public template qualification.
