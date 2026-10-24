# dev-services

Pinned PostgreSQL17.11 and Redis8.0.2 for application development, running as the sandbox user without Docker Compose or systemd.

## What it does

Initialize a private workspace database directory, start both actual servers, execute bounded SQL and selected Redis operations, inspect status and stop only owned workers. Default listeners are loopback5432/16379; command API9000. Both require a caller-supplied password. Existing unrelated data directories are rejected.

## Stack

Alibaba base fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>, defaultv0.0.49. Debian postgresql-17/client/libpq5 fixed17.11-0+deb13u1; redis-server/tools fixed5:8.0.2-3+deb13u3. Remaining OS security libraries resolve from configured Debian repositories. Server fallback e2cb27e24fde0a67112f82b8d44af463445a5d1a; an injected wheel wins. Generation2, USER user, /home/user/app, standard agent-sandbox-server serve/healthcheck; no CMD/ENTRYPOINT. Package default cluster/autostart disabled; no root runtime initdb.

## Problem solved

Provide real databases for sandboxed apps without privileged Docker, mounts or service managers, with explicit authentication, caller data preservation and independently verified process cleanup.

## Quick start (CLI)

Follow the [usage guide](../docs/using-templates.md#installation) to install the clients, configure the provider and set an independent `ABX_SERVER_TOKEN`. From this repository's root, launch the application and retain its sandbox ID. Replace `<sandbox-id>` below with that ID.

```bash
abx --provider alicloud-express template launch ./dev-services --workflow application --yes
abx run <sandbox-id> services_versions --json-args '{}'
```

`template launch` prepares and starts this instance's application. See the [complete calling flow](../docs/using-templates.md#cli-sdk-and-http) for OpenSandbox configuration, provider selection on every call and owned-resource cleanup. The next examples reuse the same running instance.

## Quick start (Python SDK)

Install `agent-sandbox-client` and follow the [Python connection example](../docs/using-templates.md#cli-sdk-and-http), using `ProviderSandbox.connect` and `application_client` with the independent application token. Replace the command call inside that example's `try` block with:

```python
print(await client.commands.run('services_versions'))
```

Keep the guide's connection and close steps. `sb.commands.run` executes a process; `client.commands.run` calls this template's named commands. Business commands, arguments and limits are listed in the command reference below.

## Quick start (HTTP POST)

Follow the [HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserve gateway headers, path and query parameters, and set the independent application token. Change the request to `POST /commands/services_versions`, with `Content-Type: application/json` and this direct argument object:

```json
{}
```

Expected response for this check:

```json
{"result": {"postgres": "17.11", "redis": "8.0.2"}}
```

`result` is buffered, not an event stream. Missing or mistyped arguments return 400, failed authentication 401, unknown commands 404, and execution errors 500. Set the HTTP wait and command deadline separately; a client timeout does not guarantee cancellation.

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
| ABX_SERVER_TOKEN | Required; empty manifest declaration | Export the independent application token before launch |
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

See [test results and scope](../docs/using-templates.md#evidence-and-providers). The dated records below identify the tested input and entry point.

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
