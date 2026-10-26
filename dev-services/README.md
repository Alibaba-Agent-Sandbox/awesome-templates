# dev-services

[中文](README.zh-CN.md)

## What it does

Initialize a private workspace database directory, start both actual servers, execute bounded SQL and selected Redis operations, inspect status and stop only owned workers. Default listeners are loopback5432/16379; command API9000. Both require a caller-supplied password. Existing unrelated data directories are rejected.

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a6`, installed directly by the Dockerfile.

Alibaba base fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>, defaultv0.0.49. Debian postgresql-17/client/libpq5 fixed17.11-0+deb13u1; redis-server/tools fixed5:8.0.2-3+deb13u3. Remaining OS security libraries resolve from configured Debian repositories.  Generation2, USER user, /home/user/app, standard agent-sandbox-server serve/healthcheck; no CMD/ENTRYPOINT. Package default cluster/autostart disabled; no root runtime initdb.

## Problem solved

Provide real databases for sandboxed apps without privileged Docker, mounts or service managers, with explicit authentication, caller data preservation and independently verified process cleanup.

## Quick start (CLI)

CLI, SDK and HTTP are alternative ways to use the same application. Choose one for the task. Examples may write files, create projects or start services; do not repeat the full example on the same instance without cleaning its previous outputs.

Install the CLI/Python SDK and configure your platform with the [usage guide](../docs/using-templates.md#installation). The platform API key creates sandboxes; `ABX_SERVER_TOKEN` independently protects this template application. Run the following in your own terminal; cloning this repository is unnecessary.

These template commands require no model, model endpoint or model API key.

Replace the password placeholder with a unique password of 16–128 URL-safe ASCII characters. It does not replace `ABX_SERVER_TOKEN`.

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export DEV_SERVICES_PASSWORD='<choose-a-long-unique-password>'
export ABX_HTTP_TIMEOUT=450
abx template launch Alibaba-Agent-Sandbox/awesome-templates//dev-services --sandbox-timeout 1800 --yes
# Paste the sandbox ID from the launch output
export SANDBOX_ID='paste-id-from-launch-output'
abx sandbox command list "$SANDBOX_ID"
```

```bash
abx run "$SANDBOX_ID" services_start --json-args '{}'
abx run "$SANDBOX_ID" services_sql --json-args '{"sql":"CREATE TABLE usage_demo (amount integer); INSERT INTO usage_demo VALUES (5130); SELECT sum(amount) AS total_cents FROM usage_demo;"}'
```

Returns PostgreSQL query output containing total `5130` cents; it creates a table in this sandbox database.

Databases listen on sandbox loopback by default. Use `services_sql` / `services_redis` without a local database login. External clients require explicit `expose=true`, appropriate port forwarding and the independent database password. Data lives in workspace `service-data/`.

`--sandbox-timeout 1800` gives the instance a 30-minute lifetime for the task and artifact export. `ABX_HTTP_TIMEOUT` controls local HTTP waiting and does not extend that lifetime. Delete the instance when finished.

For OpenSandbox, set `ABX_PROVIDER=opensandbox` and configure its [provider guide](https://github.com/Alibaba-Agent-Sandbox/awesome-providers/blob/main/opensandbox/docs/README.md). Keep the same provider selected for subsequent CLI and Python calls.

## Quick start (Python SDK)

In your virtual environment, run `python -m pip install agent-sandbox-client==0.4.0a6`.

After launching above and setting `SANDBOX_ID`, save this as `use_template.py` and run `python3 use_template.py`. It connects to the same instance instead of creating another sandbox. Prepare any input file locally as shown above.

```python
import asyncio
import os
from pathlib import Path
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.connect(
        os.environ["SANDBOX_ID"], provider=os.environ["ABX_PROVIDER"]
    )
    try:
        client = await sb.application_client(
            9000, token=os.environ["ABX_SERVER_TOKEN"], timeout=450
        )
        try:
            await client.commands.run('services_start')
            result = await client.commands.run('services_sql', sql='CREATE TABLE usage_demo (amount integer); INSERT INTO usage_demo VALUES (5130); SELECT sum(amount) AS total_cents FROM usage_demo;')
            print(result)
        finally:
            try:
                await client.commands.run('services_stop')
            finally:
                await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

The SDK returns the command value; it unwraps the HTTP `result` envelope. Closing the client does not delete the sandbox.

## Quick start (HTTP POST)

Resolve port 9000 on the same instance with the [HTTP calling example](../docs/using-templates.md#cli-sdk-and-http). Preserve gateway headers, URL path and query before adding the independent application authentication.

First call, in order:

- `POST /commands/services_start` with `{}`.

`POST /commands/services_sql`

```json
{
  "sql": "CREATE TABLE usage_demo (amount integer); INSERT INTO usage_demo VALUES (5130); SELECT sum(amount) AS total_cents FROM usage_demo;"
}
```

Use `Content-Type: application/json` and application authentication as described in the shared guide. The request body is the direct argument object, without an `args` wrapper. Success returns `{"result": ...}` with the value described above. Set the HTTP client wait to 450 seconds, separately from the command execution deadline. Responses are buffered, not event streams. Errors: 400 invalid arguments, 401 authentication, 404 unknown command, 500 execution failure.

After use, call:

- `POST /commands/services_stop` with `{}`.

## Command reference

| Command | Parameters | Returns |
|---|---|---|
| services_setup_check | none / 无 | installed flag, declared pins and password-configured boolean; no credentials |
| services_versions | none | actual {postgres,redis} semantic versions |
| services_start | password:16..128 URL-safe ASCII chars, default DEV_SERVICES_PASSWORD; data_dir: single workspace name, default service-data; expose:bool=false; timeout_s:1..120=60, applied to initialization/readiness phases | {postgres:5432,redis:16379,running:true,exposed:bool} |
| services_status | none | {running:false} or {running:bool,postgres:5432,redis:16379} |
| services_sql | sql:required1..16384UTF8 bytes | psql unaligned tuple stdout |
| services_redis | action:PING/SET/GET/DEL/INCR=PING; key:required except PING,1..1024bytes; value:SET text, max64KiB | raw Redis reply string; missing GET is empty string |
| services_stop | none | {running:false} after owned process/listener absence |
| services_self_test | none; refuses already-running owned services | POSTGRES_REDIS_OK after real SQL/Redis/restart and owned data cleanup |

psql uses -X/ON_ERROR_STOP, credentials in its process environment; redis-cli -e ensures protocol errors are failures. Both use literal argv without shell interpolation. SQL runs as the cluster user with sandbox OS permissions. Each client has30-second process and256KiB per-stream output bounds. New clusters use SCRAM-SHA-256; Redis uses mandatory requirepass. Private init password/config files have mode0600 under0700 directories. Redis memory128MiB/noeviction, PostgreSQL shared buffers64MiB/max connections20. Neither is configured for production HA.

Version1.1.0 adds postgres_port:int=0 and redis_port:int=0 to services_start. Zero selects process-start DEV_SERVICES_POSTGRES_PORT/DEV_SERVICES_REDIS_PORT; this image defaults to5432/16379. Bare independently loaded source without those settings retains5432/6379. Explicit ports must be distinct integers1024..65535 excluding command port9000. Status and start return the actual selected ports. The original1.0.0 Express attempt found6379 occupied before any owned start (independent EADDRINUSE98); no foreign listener is stopped. The1.0.0 data marker denotes the unchanged storage format and remains readable in1.1.0. API/SQL/Redis auth and process ownership remain required. [Port diagnosis](evidence/port-conflict-2026-10-20.json).

## Configuration

| Name | Default | Purpose |
|---|---|---|
| ABX_SERVER_TOKEN | empty | Export an independent application token before the template launch; separate from model and gateway credentials |
| ABX_SERVER_PORT | 9000 | local command API port |
| WORKSPACE | /home/user/app | existing workspace root |
| DEV_SERVICES_PASSWORD | empty | optional default password; per-call password also supported |
| DEV_SERVICES_POSTGRES_BIN | /usr/lib/postgresql/17/bin | trusted pinned executables |
| DEV_SERVICES_REDIS_BIN | /usr/bin | trusted pinned executables |
| DEV_SERVICES_LIBRARY_PATH | empty | trusted shared-library search path for extracted-package local tests |

Prewarmed command servers need [explicit process configuration](../docs/runtime-environment.md). Database children get filtered PATH/HOME/locale and ownership marker, without cloud/model keys. Loopback is default; expose=True deliberately adds PostgreSQL SCRAM host authorization and0.0.0.0 listeners with authentication. Caller data/passwords must be handled as private content.

The working directory is `/home/user/app`. Artifacts remain on the sandbox disk; export anything needed before deleting the instance. Delete only your own instance and the prepared template/image identified by its launch receipt.

```bash
abx run "$SANDBOX_ID" services_stop --json-args '{}'
abx kill "$SANDBOX_ID"
```

`abx kill` deletes the sandbox, not reusable prepared templates or images. Follow the [cleanup guide](../docs/using-templates.md#cli-sdk-and-http) for resources created by your launch.

## Resources

2vCPU,2048MB, about10GiB rootfs; ports9000/5432/16379. No Docker/KVM/root/display. Linux pidfds/procfs required for worker identity and independent kernel LISTEN absence. Stop sends TERM then bounded KILL; a forced stop may require PostgreSQL recovery. Redis appendonly/everysec is development durability, not a zero-loss promise. Keep backups outside ephemeral sandbox disk when needed.

## Contributing

To improve this template, see the [contribution guide](../CONTRIBUTING.md), [template specification](../docs/template-spec.md) and [design notes](../docs/design/dev-services.md).

## Issues

[Template Issue56](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/56), [Python SDK/server](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), [CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Prefix SDK/CLI reports [templates].

## License

Wrapper Apache-2.0: [LICENSE](../LICENSE). PostgreSQL uses PostgreSQL License. Redis8 supports an AGPLv3 licensing option; do not describe it as the older BSD Redis release. Installed Debian copyright and source references are retained. Review upstream/transitive notices for redistribution or modifications.
