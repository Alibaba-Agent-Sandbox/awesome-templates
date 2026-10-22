# dev-services

Pinned PostgreSQL17.11 and Redis8.0.2 for application development, running as the sandbox user without Docker Compose or systemd.

## What it does

Initialize a private workspace database directory, start both actual servers, execute bounded SQL and selected Redis operations, inspect status and stop only owned workers. Default listeners are loopback5432/16379; command API9000. Both require a caller-supplied password. Existing unrelated data directories are rejected.

## Stack

Alibaba base fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>, defaultv0.0.49. Debian postgresql-17/client/libpq5 fixed17.11-0+deb13u1; redis-server/tools fixed5:8.0.2-3+deb13u3. Remaining OS security libraries resolve from configured Debian repositories. Server fallback e2cb27e24fde0a67112f82b8d44af463445a5d1a; an injected wheel wins. Generation2, USER user, /home/user/app, standard agent-sandbox-server serve/healthcheck; no CMD/ENTRYPOINT. Package default cluster/autostart disabled; no root runtime initdb.

## Problem solved

Provide real databases for sandboxed apps without privileged Docker, mounts or service managers, with explicit authentication, caller data preservation and independently verified process cleanup.

## Quick start (CLI)

Use [native CLI setup](../docs/platform-steps.md); provide account configuration through process environment.

```bash
abx template deploy ./dev-services -y --generation 2 \
  --start-cmd 'agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py' \
  --ready-cmd 'agent-sandbox-server healthcheck --port 9000'
abx create <template-id> --detach
abx run <sandbox-id> services_self_test
abx run <sandbox-id> services_status
abx run <sandbox-id> services_stop
abx kill <sandbox-id>
abx template delete <template-id> -y
```

Use the SDK example for password-controlled persistent service usage without placing the password in shell argv. [Step preparation](../docs/platform-steps.md) is structurally supported; cloud receipts remain required. [Client-entry differences](../docs/using-templates.md#client-entry-compatibility) describe standard versus native CLI.

## Quick start (Python SDK)

Install [paired client source](../docs/python-client-installation.md), distribution agent-sandbox-client, import agent_sandbox.

```python
import asyncio
import secrets
from agent_sandbox.api.sandbox import Sandbox

async def main():
    password = secrets.token_urlsafe(24)
    sb = await Sandbox.create(template="<template-id>", timeout=300)
    try:
        print(await sb.run("services_start", password=password))
        print(await sb.run("services_sql", sql="SELECT 19+23"))
        await sb.run("services_redis", action="SET", key="example", value="42")
        print(await sb.run("services_redis", action="GET", key="example"))
        await sb.run("services_stop")
        # Save needed data after stop, before destroying the sandbox.
    finally:
        await sb.kill()

asyncio.run(main())
```

Applications inside the sandbox connect to127.0.0.1, PostgreSQL user sandbox/database postgres, and the supplied password. The same password is required when restarting its existing PostgreSQL cluster. Stop retains data; sandbox deletion does not preserve ephemeral disk. For explicit expose=True, use SDK network.get_url only for provider-supported protocol routing; external TCP forwarding has not been certified.

## Quick start (HTTP POST)

Use the command-server9000 URL from SDK network.get_url(9000). Set command-server authentication before startup if needed; see [runtime environment](../docs/runtime-environment.md).

```bash
curl --fail-with-body --request POST "$ABX_SERVER_URL/commands/services_self_test" \
  --header 'Content-Type: application/json' \
  --header "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --data '{}'
```

HTTP200 returns {"result":"POSTGRES_REDIS_OK"}. The self-test generates temporary credentials, checks real read/write/restart persistence and removes its nonce-owned data. Invalid command parameters400, unknown command404, execution errors500. A client timeout does not guarantee server-side cancellation.

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
| ABX_SERVER_TOKEN | empty | optional command-server Bearer authentication before process startup |
| ABX_SERVER_PORT | 9000 | local command API port |
| WORKSPACE | /home/user/app | existing workspace root |
| DEV_SERVICES_PASSWORD | empty | optional default password; per-call password also supported |
| DEV_SERVICES_POSTGRES_BIN | /usr/lib/postgresql/17/bin | trusted pinned executables |
| DEV_SERVICES_REDIS_BIN | /usr/bin | trusted pinned executables |
| DEV_SERVICES_LIBRARY_PATH | empty | trusted shared-library search path for extracted-package local tests |

Prewarmed command servers need [explicit process configuration](../docs/runtime-environment.md). Database children get filtered PATH/HOME/locale and ownership marker, without cloud/model keys. Loopback is default; expose=True deliberately adds PostgreSQL SCRAM host authorization and0.0.0.0 listeners with authentication. Caller data/passwords must be handled as private content.

## Resources

2vCPU,2048MB, about10GiB rootfs; ports9000/5432/16379. No Docker/KVM/root/display. Linux pidfds/procfs required for worker identity and independent kernel LISTEN absence. Stop sends TERM then bounded KILL; a forced stop may require PostgreSQL recovery. Redis appendonly/everysec is development durability, not a zero-loss promise. Keep backups outside ephemeral sandbox disk when needed.

## Verified


### Current image acceptance — 2026-10-22

| Provider | Current version and scope | Evidence |
| --- | --- | --- |
| alicloud-express | 1.1.0; regular image, actual CLI/SDK, complete HTTP 6 PASS / 0 FAIL / 0 SKIP, independent sandbox/template/private-registry cleanup | [Runtime and HTTP receipt](evidence/image-http-2026-10-20T101159Z.json) |
| opensandbox | 1.1.0; original Docker backend, every CLI/SDK named smoke, complete HTTP 6 PASS / 0 FAIL / 0 SKIP, independent SDK/container/process cleanup | [Native source image receipt](evidence/opensandbox-2026-10-22T111605Z.json) |

OpenSandbox CLI smoke uses actual `abx exec` into the guest named HTTP API. Generic `run_code` remains unsupported and `template launch` capability checks still apply. Missing model/vendor-account checks remain explicit skips in the receipts and do not establish model acceptance. [Reproduction and scope](../docs/source-image-acceptance.md).

<details>
<summary>Earlier acceptance records (original dates and scope retained)</summary>

Version1.1.0 passed genuine SDK-created Express image registration, CLI/SDK engine/self-test smoke and full required-engine HTTP6 PASS/0 FAIL/0 SKIP. Actual authenticated PostgreSQL/Redis SQL and key reads/writes, stop/restart persistence, nonce-data/process/listener cleanup and independent sandbox/template/registry absence all passed. Image defaults5432/16379 preserve the occupied foreign6379 listener. External raw TCP forwarding and other providers remain unverified.

| Version | Provider | Evidence |
| --- | --- | --- |
| 1.1.0 | alicloud-express | [SDK-created image](evidence/express-2026-10-20.json), [full HTTP6](evidence/image-http-2026-10-20T101159Z.json) |

</details>

## Secondary development

Add explicitly bounded database commands and preserve authentication and no-overwrite behavior. Read [PostgreSQL initdb](https://www.postgresql.org/docs/17/app-initdb.html), [Redis security](https://redis.io/docs/latest/operate/oss_and_stack/management/security/) and package source links in upstream-pins.json. Stop both engines before copying raw data files. The wrapper is not an extra isolation boundary around caller SQL/application code.

## Contributing

[CONTRIBUTING.md](../CONTRIBUTING.md), [spec](../docs/template-spec.md), [design](../docs/design/dev-services.md). Run actual local/HTTP tests and keyless image smoke, then real cloud/cleanup acceptance before provider qualification. Never relabel an unrun or failed database test as a pass.

## Issues

[Template Issue56](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/56), [Python SDK/server](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), [CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Prefix SDK/CLI reports [templates].

## License

Wrapper Apache-2.0: [LICENSE](../LICENSE). PostgreSQL uses PostgreSQL License. Redis8 supports an AGPLv3 licensing option; do not describe it as the older BSD Redis release. Installed Debian copyright and source references are retained. Review upstream/transitive notices for redistribution or modifications.

### Additional current-version platform-step acceptance

[Actual native steps](evidence/express-2026-10-20T130648Z.json): official READY, Python SDK creation, current CLI/SDK smoke and independently confirmed owned sandbox/template cleanup. [Full external HTTP](evidence/full-http-steps-2026-10-20T130648Z.json): 6 PASS / 0 FAIL / 0 SKIP.
