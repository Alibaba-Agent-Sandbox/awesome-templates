# dev-services

## Purpose

Real authenticated non-root PostgreSQL/Redis for sandbox application development.

## Capabilities

Initialize fresh marked data, start/query/status/stop and full self-test. Data survives stop/restart. Default loopback; explicit exposed authenticated listeners optional. No Docker/systemd/HA or claimed external TCP routing certification.

## Exposed API

Eight complete named contracts in [README](../../dev-services/README.md#command-reference). Literal postgres/initdb/psql and redis-server/redis-cli argv, bounded clients, SCRAM/requirepass, private configs and filtered credentials. services_self_test performs real persisted readback and owned project removal.

## How to build

[Dockerfile](../../dev-services/Dockerfile), Alibaba base defaultv0.0.49, PostgreSQL/client/libpq17.11-0+deb13u1 and Redis/tools5:8.0.2-3+deb13u3. Critical packages fixed, transitive OS security dependencies repo-resolved. Disable default root cluster/autostart; generation2 standard serve/health, published server package, USER user.

## Express feasibility

Feasible: yes. Limiting factor: ephemeral disk and separately unverified external TCP forwarding.2vCPU/2048MB, non-root initdb, no Docker/KVM/mount/systemd. Provider acceptance remains required.

## Risks

Caller SQL has sandbox user permissions; credentials private. Default loopback and authentication mandatory even when exposed. Preserve data on stop and reject unrelated directory reuse. PID ownership uses unique inherited marker/pidfds/unreaped groups plus independent kernel listener absence. Forced shutdown may need normal PostgreSQL recovery; Redis everysec is not zero-loss production durability. Retain PostgreSQL/Redis8 license notices.

## Test plan

Actual exact engine versions, authenticated SQL/Redis read/write, wrong-password rejection, stop/restart data readback, filtered model key, owned process/listener absence and unrelated-listener preservation. L0 external HTTP full self-test and nonce data cleanup. L1 actual installed pins plus self-test as image user. L2 real generated/image registration READY, CLI/SDK self-test, external HTTP and independently confirmed owned cleanup. No external TCP certification without a real forwarded connection.

Version1.1.0 uses explicit configurable database ports. Process-start image defaults5432/16379 avoid the independently observed pre-existing6379 listener in the actual Express sandbox; unknown listener ownership never permits signaling it. Bare source defaults retain5432/6379 for compatibility. Named arguments override only to distinct nonprivileged ports excluding9000; auth, persistence and pidfd ownership remain intact. New runtime requires new image/provider qualification. Actual local12 native tests PASS, including preservation of a foreign listener while configured Redis uses another port.
