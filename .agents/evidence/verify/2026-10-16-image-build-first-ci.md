# First actual L1 matrix and follow-up fixes

Date: 2026-10-16
Result: PARTIAL

## Tested remote revision and exact results

Head: 7289e69976a0b20045527b6aeed405062472443a, verified through GitHub API for
[PR #82](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/82).
[Actual image workflow](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/38848881611).
All 16 image checks completed. The 13 successful jobs actually built Docker images,
validated installed pins/non-root user and ran keyless container commands. They
are L1 results for this revision, not provider or model acceptance.

| Template | Actual first-run result |
|---|---|
| amp | L1 PASS |
| browser-automation | L1 PASS |
| claude-code | L1 PASS |
| codex | L1 PASS |
| codex-agent-api | L1 PASS |
| deepseek-harness | L1 PASS |
| gemini | L1 PASS |
| hermes-agent | L1 PASS |
| node-web | L1 PASS |
| opencode | L1 PASS |
| python-hello | L1 PASS |
| qoder | L1 PASS |
| qwen-code | L1 PASS |
| agents-cli | CI preparation FAIL; image build NOT RUN |
| openclaw | CI preparation FAIL; image build NOT RUN |
| droid | Actual image build FAIL |

Both actual host e2e runs completed successfully at the same head:
[PR run](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/38848881565),
[push run](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/38848877544).
These runs cover local L0; they do not establish L2 or L3.

## CI preparation failure and correction

[agents-cli job](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/38848881611/job/116805457526)
and [OpenClaw job](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/38848881611/job/116805457619)
failed before Docker execution in Prepare the standalone template context,
line 19, AssertionError. The generic case-insensitive FROM regex also matched
`from pathlib import Path` inside the Node installer Python heredoc.

The step now recognizes only the exact literal Alibaba FROM line. It changes only
its region/tag placeholders and preserves every other byte, including heredocs and
original SDK install conditionals. A regression in scripts/test_spec_tools.py
executes the actual workflow context-preparation block against all 16 real template
Dockerfiles with an opaque copy-only wheel fixture. It does not mock Docker or
claim that fixture is installable software.

PASS: exact workflow prepare code also executed against all 16 real templates using
an actual source-built server wheel. Every copied wheel matched the original
bytes; reversing only the fixed FROM string reconstructed the complete original
Dockerfile bytes. Owned temporary contexts were removed.

PASS: python scripts/test_spec_tools.py, exit 0, 22 tests. Includes the new 16-input
context regression and all existing checker/harness tests. Mock Express cases in
that unit suite remain protocol fixtures, not provider evidence.

## Droid actual image failure and correction

[Droid job](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/38848881611/job/116805457480)
failed during the real npm install/version build instruction:
`droid: Too many levels of symbolic links`. npm reported only 1 installed package.
The pinned upstream installer source shows that absent optional native packages
trigger a fallback writing bin/droid, then attempt to replace that same path by a
link, which can leave a self-referencing symlink.

Actual registry requests for @factory/cli-linux-x64/0.241.1 returned 404 from the
base mirror and 200 from registry.npmjs.org, whose metadata matched the exact package
and version. Dockerfile now explicitly uses the official registry and includes
optional packages. The exact 0.241.1 version assertion is unchanged. Bilingual
README/design explain the requirement. No unpinned upgrade or ignored build error
was introduced.

PASS: python scripts/check_template.py droid, exit 0, conformant.
PASS: scoped git diff --check and document links, exit 0.
PENDING: actual remote image rebuild after these source corrections. No local
Docker engine is available; no local image fix pass is claimed.

## Scope and privacy

The follow-up changes only image-build.yml, its existing spec-tools regression,
Droid's install/docs and owner records. No job was retriggered manually and no
second matrix was started by this review. The integrator will combine actual
source corrections in one commit. Existing evidence is preserved as history.

GitHub run/job metadata and sanitized failure excerpts were inspected using local
authentication. Tokens, signed log-download URLs and raw sensitive logs were not
retained. No cloud/model credentials were sent to GitHub. No cloud resource or
published image was created. Existing images were not yet exported as artifacts;
L2 continues separately through the verified existing-image registration path.


## Prepared single-image archive transfer

The same necessary follow-up commit prepares an export only for python-hello,
after its real build and keyless container checks succeed. docker image save
writes the already built image once; no second image build or registry push is
performed. A one-day artifact includes the Docker archive, its SHA256 and metadata
with the checkout commit, workflow run, server SDK commit, base and local image
ID. No other template exports a large archive, and no cloud/model credential is
passed into GitHub. This export is still PENDING until the next actual job runs.

Existing production CLI template create accepts a pushed image URI with explicit
generation/start/ready settings and calls createOfficialTemplate directly, without
DockerBuilder. waitForTemplateReady is available in the same API module. A local
daemonless registry client can transfer the Docker archive before registration;
that local transfer, registration and outside-sandbox smoke are distinct L2 work.
No archive download, ACR push or template creation was performed in this review.
