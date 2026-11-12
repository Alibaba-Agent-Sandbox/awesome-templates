# Retained local Qwen execution and offline verification sources

These are the exact original small scripts from the one local Docker/real-model attempt,
retained byte-for-byte; sources.json records their hashes. They are engineering reproduction
sources, not product entry points or a new execution. The host-specific capture runner,
private inputs, raw model stderr, dependency caches and images are not committed.

## Execution contract of the recorded attempt

1. Build/reuse the reviewed Guest recipe and fixtures. The actual image identity and results
   are in the [owner evidence](2026-11-12-agents-api-final-local-validation.md). A local image
   ID is an identity, not a remotely downloadable registry reference.
2. A trusted host parent supplies one JSON line to guest-driver.py on stdin with only apiKey,
   baseUrl and model. The recorded model was qwen3-coder-flash. Never put these values in Docker
   argv/environment options, a committed file or output. This is an explicit real-model action
   with costs; it is not automatically run by document checks.
3. The recorded guest was non-root with2 CPUs/2GiB/192 PIDs, all capabilities dropped and
   no-new-privileges. A fresh owned container used --rm, a read-only driver mount and an
   explicit task label. The host enforced400 seconds,3MiB stdout and64KiB stderr; the driver
   has its own bounded deadlines and emits typed outcomes plus fixed artifact payloads.
4. Decode only the fixed expected output names, verify byte lengths/SHA256 and reject any
   echoed model key before retaining downloaded data. Keep raw stderr out of the evidence.
5. Mount the downloaded first/final files read-only at the verifier's container path and run
   verify-downloads.py in a separate network-none container (recorded1 CPU/512MiB/64 PIDs,
   all capabilities dropped/no-new-privileges). Mount the unmodified
   [original test](../../../agents-api/fixtures/csv-analysis/tests/test_aggregate.py)
   at the path expected by verify-original-tests.py and independently run that verifier too.
   Those container-internal paths are intentional, not workstation paths.
6. Stop and remove only the newly recorded owned containers in a finally path, and independently
   query the task label for absence. Do not blindly remove a pre-existing container by name.
   Keep the typed summary, actual source/image hashes and any failure/uncertainty under owner
   dated evidence. The recorded attempt left no task containers; its images were retained.

The two terminal turns, independent outputs and3+3 original tests are actual prior results.
They prove the same bridge Session/workspace. Native CLI resume identity was not independently
captured, and second-turn wire event counts include replay. Do not call this FC/cloud Sandbox
E2E, all-method/API acceptance, or a Codex success.

For the actual deployment business gate, use the existing
[Gateway smoke program](../../../agents-api/scripts/smoke.py) after operator prerequisites
are ready; do not replace it with this local replay. See the
[owner operations](../../notes/proposed/process/2026-11-12-agents-api-delivery-operations.md).

## Exact local image inputs

Dockerfile.guest.resolved retains the actual materialized Express FROM and original recipe.
From the repository root, the following are **reproduction instructions, not commands executed
during this record-placement follow-up**. Select fresh owned tags and keep private configuration
out of either context:

```sh
docker build --file .agents/evidence/verify/2026-11-12-agents-api-local-replay/Dockerfile.guest.resolved --tag <fresh-owned-guest-tag> agents-api
```

For the Server, use only a newly created temporary context containing the reviewed
agents-api/server/Dockerfile, then `docker build --tag <fresh-owned-server-tag> <owned-context>`.
Do not send a project dotenv or credentials directory as context. Confirm that recipe still
pins SDK b988 and its recorded archive hash before using the historical server-final-probe.py.
Run that retained probe in the matching non-root Server image with network disabled and a
read-only script mount, supplying only the public EXPECTED_SOURCE_SHA256 value from the owner
image JSON. It checks HTTP/SQLite, the installed Core reader and in-process native serializer
fixtures; those fixtures do not call native cloud infrastructure. Run pip check independently.

Inspect any newly built image and retain its actual identity; do not assume it has the previous
local image ID. Record new outcomes/failures separately. Source-copy and syntax/hash validation
do not establish that either image or a model was rerun.
