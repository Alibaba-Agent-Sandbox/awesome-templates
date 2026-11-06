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

## L0 consumer pin follow-up

Actual workflow/source review found the main full-template local-e2e job still
installed server/clienta6, while the strict managed startup invokes
`agent_sandbox.server.managed`, absent from that release. Upgrade only this job's
two SDK pins to the public a7. Other isolated database/document/media jobsa6 pins
remain unchanged; no interpreter override or runner behavior is added. The
deployment reviewer independently accepted this narrower dependency correction.
The recipe directory at a6d37c32 remains byte-for-byte unchanged by this follow-up.
Fresh installed-a7 managed and legacy L0 results are recorded below; remote full
local-e2e remains the authority for the complete template compatibility matrix.

Installed both public a7 packages in the isolated template test environment and
ran the actual `_run_one` local runner with that environment's bin directory:
`agents-api` PASS, `python-hello` PASS (20 cases), `node-web` PASS (60 cases).
These are local process/HTTP checks with no cloud or model call. An earlier
attempt selected the environment's parent interpreter without passing its bin
path to child startup: managed collection lacked httpx and the legacy child
could not import agent_sandbox. It was recorded as an environment setup failure;
the corrected invocation changes PATH only and does not relax runtime assertions.


## Actual latest-head CI fixture correction

The remote e2e run [42204018164](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/42204018164)
on68a095b failed in `ImageBuildContextTest`, before local template startup:
its existing blanket assertion required servera6 for every recipe, conflicting
with the independently published managed recipe's explicit a7. Documentation,
Express CLI, media, document and dev-services jobs passed. The original failure
is preserved rather than relabeled as a product startup failure.

After independent deployment-review approval, the existing assertion now expects
exact a7 only for agents-api and exact a6 for every other template. It still
requires the public PyPI index, byte-for-byte materialized Dockerfile equality
apart from the known FROM substitution, and no local wheel. The expected version
is not inferred from the Dockerfile under test. No recipe or runtime bytes changed.
Actual isolated `python scripts/test_spec_tools.py`:52 tests passed in20.736s;
the printed malformed-fixture conformance errors are expected negative cases.
Latest-head remote CI must pass before merge; no prior failed run is overwritten.
