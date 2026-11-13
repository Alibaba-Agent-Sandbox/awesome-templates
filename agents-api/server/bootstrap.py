"""Translate this template's scalar FC environment into the pinned SDK bootstrap."""
from __future__ import annotations

import json
import os
import re
import sys
from collections.abc import Mapping


def document(environment: Mapping[str, str], name: str, default: str = "{}") -> dict:
    value = json.loads(environment.get(name, default))
    if not isinstance(value, dict):
        raise ValueError(f"{name} must contain a JSON object")
    return value


def compile_environment(environment: Mapping[str, str], role: str) -> dict[str, str]:
    """Separate public configuration, gateway authentication and worker secrets."""
    if role not in {"gateway", "worker", "dispatcher"}:
        raise ValueError("Unknown managed role")
    required = ["AGENTS_APPLICATION", "AGENTS_REVISION", "AGENTS_TEMPLATE", "AGENTS_MODEL", "AGENTS_ADAPTER", "ABX_MANAGED_DATABASE_URL", "ABX_MANAGED_INTERNAL_TOKEN"]
    if any(not environment.get(name) for name in required):
        raise ValueError("Managed role bootstrap is incomplete")
    if environment["AGENTS_ADAPTER"] not in {"codex", "qwen-code"}:
        raise ValueError("Choose codex or qwen-code for the model adapter")
    if len(environment["ABX_MANAGED_INTERNAL_TOKEN"]) < 32:
        raise ValueError("The internal token must have at least 32 characters")
    policy = document(environment, "AGENTS_POLICY_JSON")
    if set(policy) - {"sessions", "limits", "storage", "instance", "instanceEnvNames"}:
        raise ValueError("Unknown managed policy field")
    config = {"applicationId": environment["AGENTS_APPLICATION"], "revision": environment["AGENTS_REVISION"],
              "template": environment["AGENTS_TEMPLATE"], "models": {environment["AGENTS_MODEL"]: environment["AGENTS_ADAPTER"]},
              "provider": "alicloud-express", "workspace": "/workspace", "port": 9000,
              "workers": document(environment, "AGENTS_WORKERS_JSON"), **policy}
    state = environment.get("AGENTS_STATE_ID", "")
    if state:
        if not re.fullmatch(r"[a-f0-9]{32}", state):
            raise ValueError("The database identity must be a 32-character lowercase hex ID")
        config["expectedStateId"] = state
    result = {"ABX_MANAGED_CONFIG_JSON": json.dumps(config, separators=(",", ":"))}
    if role == "gateway":
        digest = environment.get("AGENTS_BUSINESS_SHA256", "")
        if not re.fullmatch(r"[a-f0-9]{64}", digest):
            raise ValueError("Gateway authentication digest is missing")
        result["ABX_MANAGED_AUTH_JSON"] = json.dumps({"tokens": [{"sha256": digest, "owner": "default", "scopes": ["agents:read", "agents:write"]}]}, separators=(",", ":"))
    else:
        keys = {"apiKey": "SANDBOX_API_KEY", "baseUrl": "SANDBOX_BASE_URL", "domain": "SANDBOX_DOMAIN", "region": "SANDBOX_REGION"}
        if any(not environment.get(key) for key in keys.values()):
            raise ValueError("Sandbox platform credentials and endpoints are required")
        result["ABX_MANAGED_PROVIDER_CONFIG_JSON"] = json.dumps({"provider": "alicloud-express", **{key: environment[value] for key, value in keys.items()}}, separators=(",", ":"))
        if role == "worker":
            if not environment.get("OPENAI_API_KEY") or not environment.get("OPENAI_BASE_URL", "").startswith("https://"):
                raise ValueError("An explicit model key and HTTPS endpoint are required")
            result["ABX_MANAGED_MODEL_CONFIG_JSON"] = json.dumps({"apiKey": environment["OPENAI_API_KEY"], "baseUrl": environment["OPENAI_BASE_URL"], "model": environment["AGENTS_MODEL"], "adapter": environment["AGENTS_ADAPTER"]}, separators=(",", ":"))
    return result


def main() -> None:
    role = sys.argv[1] if len(sys.argv) > 1 else "gateway"
    os.environ.update(compile_environment(os.environ, role))
    from agent_sandbox.managed_agents.models import ManagedConfig
    ManagedConfig.from_dict(json.loads(os.environ["ABX_MANAGED_CONFIG_JSON"]))
    from agent_sandbox.managed_agents.__main__ import main as serve
    sys.argv = [sys.argv[0], role, *sys.argv[2:]]
    serve()


if __name__ == "__main__":
    main()
