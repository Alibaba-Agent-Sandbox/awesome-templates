#!/usr/bin/env python3
"""Template-owned release coordination for the three native FC resources.

State and credentials stay under .abx. This program never prints remote bodies,
credentials or raw SDK exceptions, and never retries an uncertain mutation.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import hmac
import io
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / ".abx" / "agents-api"
STATE = PRIVATE / "release.json"
ROLES = ("worker", "dispatcher", "gateway")


class ReleaseError(Exception):
    """Safe actionable deployment error."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReleaseError(message)


def read(path: Path, default=None):
    if not path.exists():
        return default
    require(not path.is_symlink() and path.is_file(), "Private deployment input must be a regular file")
    return json.loads(path.read_text())


def save(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    require(not path.is_symlink(), "Private deployment output must not be a symlink")
    temporary = path.with_name(path.name + ".tmp-" + secrets.token_hex(4))
    fd = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w") as stream:
        stream.write(json.dumps(value, separators=(",", ":")) + "\n")
        stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, path)


@contextlib.contextmanager
def lock():
    PRIVATE.mkdir(parents=True, exist_ok=True, mode=0o700)
    target = PRIVATE / "release.lock"
    try:
        descriptor = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise ReleaseError("Another release owns .abx/agents-api/release.lock; inspect it before recovery") from None
    try:
        os.write(descriptor, str(os.getpid()).encode()); os.close(descriptor)
        yield
    finally:
        target.unlink()


def dotenv() -> dict[str, str]:
    """Read simple generated assignments without shell execution or interpolation."""
    result = {}
    path = ROOT / ".env"
    if path.exists():
        require(not path.is_symlink() and path.is_file(), ".env must be a regular file")
        for line in path.read_text().splitlines():
            match = re.fullmatch(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*", line)
            if match:
                value = match[2]
                if value.startswith('"'):
                    try: value = json.loads(value)
                    except ValueError: value = value.strip('"')
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                result[match[1]] = value
    return result


def environment() -> dict[str, str]:
    return {**dotenv(), **os.environ}


def write_generated(values: dict[str, str]) -> None:
    path = ROOT / ".env"
    require(not path.is_symlink(), ".env must not be a symlink")
    lines = path.read_text().splitlines() if path.exists() else []
    lines = [line for line in lines if not any(re.match(r"\s*" + re.escape(key) + r"\s*=", line) for key in values)]
    lines.extend(f"{key}={json.dumps(value)}" for key, value in values.items())
    temporary = PRIVATE / "generated.env"
    descriptor = os.open(temporary, os.O_CREAT | os.O_TRUNC | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0), 0o600)
    with os.fdopen(descriptor, "w") as stream:
        stream.write("\n".join(lines) + "\n"); stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, path)


def validate_policy(policy: dict) -> None:
    require(isinstance(policy, dict) and not set(policy) - {"sessions", "limits", "storage", "instance", "instanceEnvNames"}, "Unknown managed policy field")
    sessions, limits, storage = (policy.get(key, {}) for key in ("sessions", "limits", "storage"))
    allowed = {
        "sessions": {"idleTimeoutSeconds", "maxLifetimeSeconds", "maxLogicalSessionsPerOwner", "maxActiveSessions", "maxQueuedTurnsPerSession", "resultRetentionSeconds", "maxConcurrentTurnsPerSession"},
        "limits": {"maxRunSeconds", "maxToolSeconds", "maxConcurrentRuns", "maxQueuedRuns", "maxRunsPerMinute", "maxEventsPerRun", "maxOutputBytes", "maxSubscribersPerSession"},
        "storage": {"maxFileBytes", "maxArtifactBytes", "maxTurnArtifactBytes", "maxRetainedBytesPerOwner"},
    }
    for name, values in (("sessions", sessions), ("limits", limits), ("storage", storage)):
        require(isinstance(values, dict) and not set(values) - allowed[name] and all(type(value) is int and value > 0 for value in values.values()), "Managed budgets must be known positive integers")
    require(isinstance(policy.get("instance", {}), dict), "Instance policy must be an object")
    lifetime = policy.get("instance", {}).get("timeout", sessions.get("maxLifetimeSeconds", 3600))
    require(type(lifetime) is int and lifetime > 0, "Instance lifetime must be positive")
    require(sessions.get("idleTimeoutSeconds", 900) <= lifetime and sessions.get("maxConcurrentTurnsPerSession", 1) == 1, "Sessions require one active turn and idle timeout within lifetime")
    require(limits.get("maxToolSeconds", 60) <= limits.get("maxRunSeconds", 600) <= lifetime, "Tool and run budgets must fit the Session lifetime")
    require("maxLifetimeSeconds" not in sessions or sessions["maxLifetimeSeconds"] == lifetime, "Instance timeout and Session lifetime must agree")
    # This recipe intentionally exposes a single lifetime knob; other instance controls belong in a reviewed recipe.
    require(isinstance(policy.get("instance", {}), dict) and not set(policy.get("instance", {})) - {"timeout"}, "This recipe supports instance.timeout only")
    require(not policy.get("instanceEnvNames"), "Add guest environment forwarding in both the worker and template recipe before declaring names")


def initialize(name: str, region: str) -> None:
    import yaml
    require(bool(re.fullmatch(r"[a-z][a-z0-9-]{0,31}", name)), "Use an application name of up to 32 lowercase letters, digits or hyphens")
    require(bool(re.fullmatch(r"[a-z]+(?:-[a-z0-9]+)+", region)), "Use an explicit FC region")
    env = environment()
    for key in ("AGENTS_SERVER_IMAGE", "ABX_MANAGED_DATABASE_URL", "SANDBOX_API_KEY", "SANDBOX_BASE_URL", "SANDBOX_DOMAIN", "SANDBOX_REGION", "OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL", "AGENTS_FC_ROLE_ARN"):
        require(bool(env.get(key)), f"Set {key} before deploying this template")
    image = env["AGENTS_SERVER_IMAGE"]
    require("/" in image and ":" in image.rsplit("/", 1)[-1] and "@" not in image and not image.endswith(":latest"), "Use an explicit unique Server image tag, not latest or a digest build target")
    require(env["ABX_MANAGED_DATABASE_URL"].startswith(("postgres://", "postgresql://")), "Use an existing PostgreSQL database")
    require(env["OPENAI_BASE_URL"].startswith("https://") and env["SANDBOX_BASE_URL"].startswith("https://"), "Sandbox and model endpoints must use HTTPS")
    manifest = yaml.safe_load((ROOT / "template.yaml").read_text())
    policy = manifest["vars"]["policy"]
    validate_policy(policy)
    old = read(STATE, {})
    require(not old or (old["application"] == name and old["region"] == region), "Application identity or region changed; use another project directory")
    require(old.get("status") not in {"publishing", "requires_reconcile", "draining", "removed"}, "A previous release is unconfirmed; inspect scripts/release.py status before recovery")
    if old.get("status") == "ready":
        require(image not in {entry.get("image") for entry in [*old.get("history", []), old.get("current", {})]}, "Choose a new Server image tag so retained revisions keep their original image")
    elif old.get("status") == "preparing":
        require(old.get("image") == image, "An unfinished release must keep its prepared Server image target")
    credentials_path = PRIVATE / "credentials.json"
    saved = read(credentials_path, {})
    generated = {}
    for key, field in (("AGENTS_BUSINESS_KEY", "businessKey"), ("AGENTS_INTERNAL_TOKEN", "internalToken")):
        if not env.get(key):
            saved.setdefault(field, secrets.token_urlsafe(32))
            generated[key] = saved[field]
        elif key not in os.environ and env[key] == saved.get(field):
            generated[key] = saved[field]
    if saved: save(credentials_path, saved)
    resolved = {**env, **generated}
    require(all(len(resolved[key]) >= 32 for key in ("AGENTS_BUSINESS_KEY", "AGENTS_INTERNAL_TOKEN")), "Business and internal tokens must each contain at least 32 characters")
    require(resolved["AGENTS_BUSINESS_KEY"] != resolved["AGENTS_INTERNAL_TOKEN"], "Business and internal tokens must be different")
    internal_digest = hashlib.sha256(resolved["AGENTS_INTERNAL_TOKEN"].encode()).hexdigest()
    require(not old.get("internalDigest") or old["internalDigest"] == internal_digest, "Internal token rotation requires a separate coordinated migration of retained revisions")
    if old.get("status") == "preparing":
        pending = old
    else:
        history = [*old.get("history", []), *([old["current"]] if old.get("current") else [])]
        revision = "rev-" + secrets.token_hex(10)
        pending = {"application": name, "region": region, "status": "preparing", "phase": "resources", "revision": revision, "image": image,
                   "functions": {"gateway": name + "-gateway", "worker": name + "-worker-" + revision, "dispatcher": name + "-dispatch-" + revision},
                   "history": history, "previous": old.get("current"), "stateInstanceId": old.get("stateInstanceId")}
        save(STATE, pending)
    pending["internalDigest"] = internal_digest
    save(STATE, pending)
    workers = {entry["revision"]: entry["functions"]["worker"] for entry in pending["history"]}
    workers[pending["revision"]] = pending["functions"]["worker"]
    generated.update({"AGENTS_REVISION": pending["revision"], "AGENTS_WORKERS_JSON": json.dumps(workers, separators=(",", ":")),
                      "AGENTS_POLICY_JSON": json.dumps(policy, separators=(",", ":")), "AGENTS_STATE_ID": pending.get("stateInstanceId") or "",
                      "AGENTS_BUSINESS_SHA256": hashlib.sha256(resolved["AGENTS_BUSINESS_KEY"].encode()).hexdigest()})
    write_generated(generated)
    print("Prepared private credentials and a release revision; no cloud resources created.")


def signed(payload: dict, token: str) -> dict:
    body = {"version": 1, "role": "dispatcher", "payload": payload}
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return {**body, "signature": hmac.new(token.encode(), canonical.encode(), hashlib.sha256).hexdigest()}


class FC:
    """Official SDK transport; no SDK retry and bounded responses."""
    def __init__(self, region: str):
        from alibabacloud_credentials.client import Client as Credentials
        from alibabacloud_fc20230330.client import Client
        from alibabacloud_tea_openapi.models import Config
        from alibabacloud_fc20230330 import models
        from darabonba.runtime import RuntimeOptions
        self.models = models
        self.runtime = RuntimeOptions(autoretry=False, connect_timeout=10000, read_timeout=30000)
        self.client = Client(Config(credential=Credentials(), endpoint=f"fcv3.{region}.aliyuncs.com"))

    def model(self, name, **kwargs):
        return getattr(self.models, name)(**kwargs)

    def call(self, method, *args):
        response = getattr(self.client, method + "_with_options")(*args, {}, self.runtime)
        return response.body.to_map() if response.body else {}

    def optional(self, method, *args):
        try: return self.call(method, *args)
        except Exception as error:
            if getattr(error, "code", None) in {"FunctionNotFound", "AliasNotFound", "TriggerNotFound"}:
                return None
            raise

    def function(self, name):
        return self.call("get_function", name, self.model("GetFunctionRequest"))

    def settled(self, name):
        for _ in range(60):
            value = self.function(name)
            require(value.get("lastUpdateStatus") != "Failed" and value.get("state") != "Failed", "FC resource preparation failed")
            if value.get("lastUpdateStatus") in {None, "Successful"} and value.get("state") in {None, "Active"}:
                return value
            time.sleep(2)
        raise ReleaseError("FC resource did not become ready within the deployment deadline")

    def patch(self, name, changes):
        value = self.settled(name)
        env = {**value.get("environmentVariables", {}), **changes}
        self.call("update_function", name, self.model("UpdateFunctionRequest", body=self.model("UpdateFunctionInput", environment_variables=env)))
        result = self.settled(name)
        require(result.get("environmentVariables") == env, "FC runtime configuration readback did not match")
        return result

    def control(self, name, payload, token):
        request = self.model("InvokeFunctionRequest", body=io.BytesIO(json.dumps(signed(payload, token), separators=(",", ":")).encode()))
        response = self.client.invoke_function_with_options(name, request, self.model("InvokeFunctionHeaders", x_fc_invocation_type="Sync", x_fc_log_type="None"), self.runtime)
        require(response.status_code == 200, "Private control invocation did not complete")
        raw = response.body.read(65537)
        require(len(raw) <= 65536, "Private control response exceeded its size limit")
        result = json.loads(raw)
        require(isinstance(result, dict) and not any(key.lower().startswith("error") for key in result), "Private control invocation returned an error")
        return result

    def trigger(self, name, trigger, qualifier, kind, config):
        current = self.optional("get_trigger", name, trigger)
        if current:
            require(current.get("triggerType") == kind and current.get("qualifier") == qualifier, "Existing trigger has a different identity")
            self.call("update_trigger", name, trigger, self.model("UpdateTriggerRequest", body=self.model("UpdateTriggerInput", qualifier=qualifier, trigger_config=json.dumps(config))))
        else:
            self.call("create_trigger", name, self.model("CreateTriggerRequest", body=self.model("CreateTriggerInput", trigger_name=trigger, trigger_type=kind, qualifier=qualifier, trigger_config=json.dumps(config))))
        observed = self.call("get_trigger", name, trigger)
        raw = observed.get("triggerConfig")
        observed_config = json.loads(raw) if isinstance(raw, str) else raw
        require(isinstance(observed_config, dict) and all(observed_config.get(key) == value for key, value in config.items()), "Trigger configuration readback did not match")
        return observed


def phase(state: dict, name: str) -> None:
    state["phase"] = name
    save(STATE, state)


def reserve(role: str) -> None:
    state = read(STATE)
    require(bool(state) and state["status"] == "preparing", "Prepare the release before deploying functions")
    fc = FC(state["region"])
    current = fc.optional("get_function", state["functions"][role], fc.model("GetFunctionRequest"))
    if current:
        prior = state.get("previous") if role == "gateway" else None
        expected = prior.get("identities", {}).get(role) if prior else state.get("identities", {}).get(role)
        require(bool(expected) and current.get("functionId") == expected, "Function already exists without this release's ownership record")


def observed(role: str) -> None:
    state = read(STATE)
    value = FC(state["region"]).settled(state["functions"][role])
    require(value.get("description") == f"Agent Sandbox {state['application']} {state['revision']}", "Deployed role does not match this release")
    require(bool(value.get("functionId")), "FC did not return a stable function identity")
    require(not state.get("identities", {}).get(role) or state["identities"][role] == value["functionId"], "Recorded FC function identity changed")
    state.setdefault("identities", {})[role] = value["functionId"]
    save(STATE, state)


def health(endpoint: str, revision: str) -> None:
    import httpx
    require(endpoint.startswith("https://"), "FC did not return an HTTPS endpoint")
    for _ in range(15):
        response = httpx.get(endpoint.rstrip("/") + "/health", timeout=15, follow_redirects=False)
        if response.status_code == 200 and response.json().get("revision") == revision:
            return
        require(response.status_code in {200, 502, 503, 504}, "Gateway readiness returned an unexpected status")
        time.sleep(2)
    raise ReleaseError("Gateway readiness did not confirm this revision")


def publish() -> None:
    state = read(STATE)
    require(state and state["status"] == "preparing", "Release publication is not safely repeatable; inspect the saved phase before recovery")
    env = environment(); token = env["AGENTS_INTERNAL_TOKEN"]
    fc = FC(state["region"])
    for role in ROLES:
        observed(role)
    state = read(STATE); state["status"] = "publishing"; phase(state, "bootstrap-state")
    status = fc.control(state["functions"]["dispatcher"], {"operation": "status", "applicationId": state["application"]}, token)
    identity = status.get("stateInstanceId")
    require(bool(re.fullmatch(r"[a-f0-9]{32}", str(identity))) and status.get("draining") is False, "Database identity or admission state could not be confirmed")
    require(not state.get("stateInstanceId") or state["stateInstanceId"] == identity, "Database identity changed; publication withheld")
    state["stateInstanceId"] = identity; phase(state, "pin-state")
    for role in ROLES:
        fc.patch(state["functions"][role], {"AGENTS_STATE_ID": identity})
    write_generated({"AGENTS_STATE_ID": identity})
    gateway = state["functions"]["gateway"]
    phase(state, "switch-dispatch")
    timer = {"cronExpression": "@every 1m", "enable": True, "payload": json.dumps(signed({"limit": 20}, token), separators=(",", ":"))}
    fc.trigger(state["functions"]["dispatcher"], "abx-dispatch", "LATEST", "timer", timer)
    if state.get("previous"):
        previous = state["previous"]["functions"]["dispatcher"]
        fc.trigger(previous, "abx-dispatch", "LATEST", "timer", {**timer, "enable": False})
    phase(state, "candidate-version")
    version = fc.call("publish_function_version", gateway, fc.model("PublishFunctionVersionRequest", body=fc.model("PublishVersionInput", description=f"Agent Sandbox {state['revision']}")))["versionId"]
    state["version"] = version; phase(state, "candidate-trigger")
    candidate = "verify-" + state["revision"][4:]
    state["candidateTrigger"] = candidate; save(STATE, state)
    http_config = {"authType": "anonymous", "methods": ["GET", "POST", "DELETE", "HEAD", "OPTIONS"], "disableURLInternet": False}
    endpoint = fc.trigger(gateway, candidate, version, "http", http_config)["httpTrigger"]["urlInternet"]
    state["candidateEndpoint"] = endpoint; phase(state, "candidate-check")
    health(endpoint, state["revision"])
    stop, errors = threading.Event(), []
    def tick():
        while not stop.is_set():
            try: fc.control(state["functions"]["dispatcher"], {"limit": 20}, token)
            except Exception: errors.append(True); return
            stop.wait(1)
    thread = threading.Thread(target=tick, daemon=True); thread.start()
    try:
        check = subprocess.run([sys.executable, str(ROOT / "scripts/smoke.py")], cwd=ROOT, env={**os.environ, "AGENTS_API_BASE_URL": endpoint, "AGENTS_API_KEY": env["AGENTS_BUSINESS_KEY"]}, timeout=900)
        require(check.returncode == 0 and not errors, "Candidate business verification failed; stable ingress was not changed")
    finally:
        stop.set(); thread.join(timeout=35)
    phase(state, "publish-alias")
    alias = fc.optional("get_alias", gateway, "prod")
    expected = state.get("previous", {}).get("version") if state.get("previous") else None
    require((alias or {}).get("versionId") == expected, "Stable alias changed or is not owned by this application")
    if alias:
        fc.call("update_alias", gateway, "prod", fc.model("UpdateAliasRequest", body=fc.model("UpdateAliasInput", version_id=version)))
    else:
        fc.call("create_alias", gateway, fc.model("CreateAliasRequest", body=fc.model("CreateAliasInput", alias_name="prod", version_id=version)))
    require(fc.call("get_alias", gateway, "prod").get("versionId") == version, "Stable alias publication is unconfirmed")
    phase(state, "stable-trigger")
    endpoint = fc.trigger(gateway, "abx-gateway", "prod", "http", http_config)["httpTrigger"]["urlInternet"]
    state["endpoint"] = endpoint; phase(state, "stable-readiness"); health(endpoint, state["revision"])
    phase(state, "candidate-cleanup"); fc.call("delete_trigger", gateway, candidate)
    require(fc.optional("get_trigger", gateway, candidate) is None, "Candidate trigger cleanup is unconfirmed")
    state["current"] = {key: state[key] for key in ("revision", "functions", "identities", "version", "endpoint", "image")}
    state["status"] = "ready"; phase(state, "ready")
    print("Application ready. Read the endpoint in .abx/agents-api/release.json and the business key in credentials.json.")


def control(operation: str, revision: str | None = None) -> None:
    state = read(STATE)
    require(bool(state), "No local release record exists")
    fc = FC(state["region"]); token = environment()["AGENTS_INTERNAL_TOKEN"]
    payload = {"operation": operation, "applicationId": state["application"], **({"revision": revision} if revision else {})}
    dispatcher = state["functions"]["dispatcher"]
    expected = state.get("identities", {}).get("dispatcher")
    require(bool(expected) and fc.function(dispatcher).get("functionId") == expected, "Dispatcher identity changed or ownership has not been confirmed")
    expected_state = state.get("stateInstanceId")
    require(bool(expected_state), "Database identity has not been pinned; destruction is not authorized")
    status = fc.control(dispatcher, {**payload, "operation": "status"}, token)
    require(status.get("stateInstanceId") == expected_state, "Database identity changed; control operation withheld")
    result = status if operation == "status" else fc.control(dispatcher, payload, token)
    require(result.get("stateInstanceId") == expected_state, "Database identity changed during control; preserve resources")
    print(json.dumps({"status": state["status"], "phase": state["phase"], **{key: result[key] for key in ("activeSessions", "pendingCleanup", "uncertainResources", "draining")}}))
    if operation == "drain":
        require(result.get("draining") is True and all(result.get(key) == 0 for key in ("activeSessions", "pendingCleanup", "uncertainResources")), "Drain is not complete; retain resources and close or reconcile the remaining sessions")
        if revision:
            state.setdefault("drainedRevisions", []).append(revision)
        else:
            state["drainConfirmed"] = True; state["status"] = "draining"
        save(STATE, state)



def destroy() -> None:
    """Drain application-owned Sessions before asking abx to remove owned resources."""
    control("drain")
    state = read(STATE)
    require(state.get("drainConfirmed") is True, "Application cleanup has not been confirmed")
    result = subprocess.run(["abx", "delete", state["application"], "--yes"], cwd=ROOT)
    require(result.returncode == 0, "Resource removal is incomplete; retain the private release record and retry destruction")
    state["status"] = "removed"; phase(state, "removed")
    print("Owned application resources removed. Existing database, execution role and supplied images remain yours.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    init = sub.add_parser("init"); init.add_argument("--name", required=True); init.add_argument("--region", required=True)
    for operation in ("reserve", "observed"):
        sub.add_parser(operation).add_argument("role", choices=ROLES)
    sub.add_parser("publish")
    sub.add_parser("destroy")
    for operation in ("status", "drain"):
        sub.add_parser(operation).add_argument("--revision")
    args = parser.parse_args()
    try:
        with lock():
            if args.operation == "init": initialize(args.name, args.region)
            elif args.operation == "reserve": reserve(args.role)
            elif args.operation == "observed": observed(args.role)
            elif args.operation == "publish": publish()
            elif args.operation == "destroy": destroy()
            else: control(args.operation, args.revision)
        return 0
    except Exception as error:
        state = read(STATE, {})
        if state.get("status") == "publishing":
            state["status"] = "requires_reconcile"; save(STATE, state)
        print(str(error) if isinstance(error, ReleaseError) else "Release operation failed or its outcome is uncertain; inspect the saved phase without repeating publication", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
