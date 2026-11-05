# Managed Agents template: source contract and local bridge verification

Date: 2026-11-05 UTC. Issue: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/295.
Base: awesome-templates `9a8e8e91bba82cff2d996b33d9c90bc2be4498ac`.
Branch: `feat/managed-agents-template-20261105`. This record is source verification,
not a published-package, image, FC or real-model acceptance receipt.

## Review and scope

The parent architecture review and independent runtime/CLI cross reviews approved
a closed spec6 profile, new managed bridge identity, per-session ownership,
server image/build exclusivity and role-bound references. Spec5 and its schema
remain unchanged. An existing old migration test that rewrote every catalog
entry to5 failed after adding6; it now tests its actual spec5 migration scope.
The independent6 suite proves both retaining6 and explicitly downgrading its
content to5 are rejected by the wrong contract.

Independent reviews confirmed the new guest has no commands-list route. L0 and
L1 therefore start the actual managed module and test its own HTTP contract;
`agents_version()` remains a local diagnostic. Legacy public single-Sandbox
acceptance explicitly refuses this application; its all selection remains46
spec5 templates and marks managed applications excluded/unverified.

The Gateway-only Python documentation uses httpx. The checker exception is limited
to explicit spec6 managed-bridge-v1; the old SDK requirement remains for spec5.
CLI default generated business/internal credential bindings are separate from
model/platform credentials, saved by apply in the CLI's private store. Template
private inputs and receipts are under ignored `.abx/`, excluded from image context.

## Actual local checks

Environment: Python3.13, separate `/tmp/agents-template-venv-20261105`; pinned
PyYAML6.0.3, jsonschema4.26.0, httpx0.28.1, pytest9.1.1. No parent verification
venv was modified. Commands were run in the isolated owning worktree.

| Command/check | Actual result | Scope |
| --- | --- | --- |
| `python scripts/test_spec_tools.py` | 48 passed | Old39 plus9 managed schema/startup tests; negative fixtures intentionally print conformance errors. |
| `python -m unittest discover -s scripts -p test_public_launch_e2e.py` | 42 passed | Legacy acceptance, ownership and explicit app rejection; no cloud operation. |
| `python -m unittest discover -s scripts -p test_canonical_express_review.py` | 6 passed | Authorization and single-Sandbox scope; planning only. |
| `python scripts/check_template.py --all` | 48 directories conformant, zero violations | Includes47 catalog source templates and `_skeleton`; not provider qualification. |
| `python -m pytest -q agents-api/test_smoke.py scripts/test_check_docs.py scripts/test_select_image_templates.py scripts/test_ci_image.py scripts/test_ci_image_archive.py scripts/test_template_http_acceptance.py` | 125 passed | Independent CSV false-result rejection, cleanup failure ordering, image/helper/HTTP regressions. |
| `python scripts/check_docs.py` | 232 documents, zero local-link failures | No network execution of examples. |
| L1 workflow YAML parse and compile extracted host/child Python | Passed | Syntax only; Docker jobs not executed. |
| `git diff --check` | Passed | Whitespace only. |

The managed cleanup regression proves that failed Close does not skip independent
Session/File delete attempts, active delete409 remains a failure, successful
business followed by cleanup failure cannot pass, and the primary business error
is preserved. These use a controlled transport; they are not an actual failed
cloud cleanup demonstration.

## Actual source L0 and readiness

Installed the runtime worktree's server-sdk with editable `pip install --no-deps
-e .../server-sdk` in this child venv. The installed metadata still says0.4.0a6;
this is modified source, explicitly not the published0.4.0a6 artifact.

Called `scripts.run_local_e2e._run_one(Path('agents-api'), '')` with the venv PATH.
It starts `python -m agent_sandbox.server.managed --port <ephemeral>` selected
from the actual manifest, using temporary state/workspace and a fresh random
token. Actual HTTP checks passed: health protocol/epoch, missing/wrong token401,
authorized capability/durable receipt declaration, and commands/core/shell/files
GET routes404. No model turn or provider API was requested.

The final repeated run hashed runtime source before and after and required no
change during execution:

- `managed.py`: `e8f94669d5867ba6d6f7c453e6b3e337ec29b86aaf4c04d59441c4837e54b88e`.
- `managed_process.py`: `fefc181cf75c3fa3307ec7efdc572d64b762e67c30ddd3690c76b720647e3677`.

Separately started that module with isolated HOME/state/workspace/token and ran
the manifest's real `agent-sandbox-server healthcheck --port <ephemeral>` console
command: exit0. All owned local bridge processes were terminated and waited;
temporary directories were removed by their context owners.

Failures were retained and corrected rather than counted as passes:

- The first imported `_run_one` failed because the new helper used script-only
  imports. An independently reviewed `__package__` relative-import branch and a
  package-entry regression fixed this; direct script imports remain tested.
- The first additional manual readiness probe raised RemoteDisconnected. No root
  cause was established. The bridge L0 and a separate clean-environment,
  no-proxy readiness run passed. This is not a cloud incident diagnosis.

## Public dependency gate: blocked

Fetched official PyPI JSON and exact0.4.0a6 wheels, validated each downloaded
wheel against PyPI's declared SHA256 and inspected its ZIP members. At this run,
both latest releases were0.4.0a6 and the required modules were absent:

| Distribution | Public wheel SHA256 | Required module |
| --- | --- | --- |
| agent-sandbox-server0.4.0a6 | `85b937438acf943b3d92736dd6a07c4829cd80416336da35c0b25f2e5679850d` | `agent_sandbox/server/managed.py` absent |
| agent-sandbox-client0.4.0a6 | `0a4d9c4b322b1e28b4dc4bc9c4a36b867232afc61fa87b483cae65f4eebb9222` | `agent_sandbox/managed_agents/__init__.py` absent |

Sources: https://pypi.org/pypi/agent-sandbox-server/json and
https://pypi.org/pypi/agent-sandbox-client/json. The two public recipes keep real
exact pins and explicit module import guards. There is no source archive/wheel
fallback and no invented next-release pin. Their public build remains blocked
until a compatible runtime is actually released and selected.

## Required remaining acceptance

The full shared runtime and CLI suites, official SDK/CLI release gates, both
original recipe image builds, current-public installation, real PostgreSQL/FC
apply/update/retire/reconcile/destroy, all39 public operations, genuine Agent
model/tool/continuation/artifacts, targeted cancellation/stop uncertainty,
restart/delivery/queue/isolation/limits/SSE, and independent owned cloud cleanup
are not established by this source record. Gateway afterReady's CSV task is a
bounded business check, not the entire acceptance matrix. No provider pass is
added and the catalog remains experimental. Later runs must use new evidence.
