"""Validate supported manifests without executing hooks, adapters, or cloud APIs."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "spec" / "template-v5.schema.json"
MANAGED_SCHEMA_PATH = SCHEMA_PATH.with_name("template-v6.schema.json")


def is_managed_application(data: dict[str, Any]) -> bool:
    """Identify only the explicit managed bridge contract, never a legacy route."""
    application = data.get("application")
    runtime = application.get("runtime") if isinstance(application, dict) else None
    return (type(data.get("spec_version")) is int and data["spec_version"] == 6
            and isinstance(runtime, dict) and runtime.get("profile") == "managed-bridge-v1")


def validate_manifest(data: dict[str, Any], template_dir: Path | None = None) -> list[str]:
    """Dispatch a declared supported version without weakening its contract."""
    if type(data.get("spec_version")) is int and data["spec_version"] == 6:
        return validate_v6(data, template_dir)
    return validate_v5(data, template_dir)


def validate_v6(data: dict[str, Any], template_dir: Path | None = None) -> list[str]:
    """Validate the closed managed-session profile and its role/source boundaries."""
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return ["v6 validation needs jsonschema==4.26.0; install scripts/requirements-spec.txt"]
    if type(data.get("spec_version")) is not int or data["spec_version"] != 6:
        return ["managed application requires spec_version: 6"]
    schema = json.loads(MANAGED_SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = [f"{'.'.join(map(str, error.absolute_path)) or '<root>'}: {error.message}"
              for error in Draft202012Validator(schema).iter_errors(data)]
    if errors:
        return errors
    for service_id, service in data["provides"].items():
        if service["port"] not in data["ports"]:
            errors.append(f"provides.{service_id}.port must be declared in ports")
    services = data["provides"].values()
    if not any(service["protocol"] == "agent-sandbox-managed-bridge"
               and service["version"] == 1 and service["port"] == 9000 for service in services):
        errors.append("managed bridge profile must provide agent-sandbox-managed-bridge v1 on port 9000")
    app = data["application"]
    limits, sessions, storage = app["limits"], app["sessions"], app["storage"]
    if limits["maxToolSeconds"] > limits["maxRunSeconds"]:
        errors.append("application.limits.maxToolSeconds must not exceed maxRunSeconds")
    if limits["maxRunSeconds"] >= sessions["maxLifetimeSeconds"]:
        errors.append("application.sessions.maxLifetimeSeconds must exceed maxRunSeconds for bounded collection/cleanup")
    if sessions["idleTimeoutSeconds"] > sessions["maxLifetimeSeconds"]:
        errors.append("application.sessions.idleTimeoutSeconds must not exceed maxLifetimeSeconds")
    if storage["maxArtifactBytes"] > storage["maxTurnArtifactBytes"]:
        errors.append("application.storage.maxArtifactBytes must not exceed maxTurnArtifactBytes")
    if max(storage["maxFileBytes"], storage["maxTurnArtifactBytes"]) > storage["maxRetainedBytesPerOwner"]:
        errors.append("application.storage per-file/turn budget must not exceed maxRetainedBytesPerOwner")
    bindings = app["bindings"]
    for label, target in (("state.bindingRef", app["state"]["bindingRef"]),
                          ("deployment.ingressBindingRef", app["deployment"]["ingressBindingRef"])):
        if target not in bindings:
            errors.append(f"application.{label} must name an application.bindings key")
    required_targets = [
        (app["state"]["bindingRef"], {"gateway", "worker", "dispatcher"}),
        (app["deployment"]["ingressBindingRef"], {"deployment-publisher"}),
        ("sandboxAccess", {"worker", "dispatcher"}), ("clientAuth", {"gateway"}),
        ("internalAuth", {"gateway", "worker", "dispatcher"}), ("model", {"sandbox-creation"}),
    ]
    for name, targets in required_targets:
        if name in bindings and set(bindings[name]["targets"]) != targets:
            errors.append(f"application.bindings.{name}: targets must be {', '.join(sorted(targets))}")
    for name, binding in bindings.items():
        targets = set(binding["targets"])
        if "sandbox-creation" in targets:
            if targets != {"sandbox-creation"} or binding.get("resolverRole") != "worker":
                errors.append(f"application.bindings.{name}: sandbox-creation binding needs only that target and worker resolver")
            allowed = {"OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL", "CODEX_API_KEY"}
            if not binding.get("allowedEnv") or not set(binding["allowedEnv"]).issubset(allowed):
                errors.append(f"application.bindings.{name}: guest injection needs an explicit model-only allowedEnv")
        elif "allowedEnv" in binding or "resolverRole" in binding:
            errors.append(f"application.bindings.{name}: guest injection fields require sandbox-creation target")
    sources: list[tuple[str, str, bool]] = []
    recipe = app["deployment"].get("serverBuildRecipe")
    if recipe is not None:
        sources.append(("deployment.serverBuildRecipe.dockerfile", recipe["dockerfile"], False))
    seen = set()
    for phase, hooks in app.get("hooks", {}).items():
        for hook in hooks:
            if hook["id"] in seen:
                errors.append(f"application.hooks: duplicate hook id {hook['id']!r}")
            seen.add(hook["id"])
            if hook["type"] == "custom":
                sources.append((f"hooks.{phase}.{hook['id']}.cwd", hook["cwd"], True))
    if template_dir is not None:
        root = template_dir.resolve()
        for label, source, directory in sources:
            try:
                path = (root / source).resolve()
            except (OSError, RuntimeError):
                errors.append(f"application.{label}: cannot resolve source path")
                continue
            if not path.is_relative_to(root):
                errors.append(f"application.{label}: source must stay inside the template directory")
            elif (directory and not path.is_dir()) or (not directory and not path.is_file()):
                errors.append(f"application.{label}: referenced {'directory' if directory else 'file'} does not exist")
    return errors


def validate_v5(data: dict[str, Any], template_dir: Path | None = None) -> list[str]:
    """Return schema/semantic errors; optional source checks stay under the template root."""
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return ["v5 validation needs jsonschema==4.26.0; install scripts/requirements-spec.txt"]
    if data.get("spec_version") != 5:
        return ["template requires spec_version: 5; migrate by removing workflow_contract_version, default_workflow and workflows"]
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = [f"{'.'.join(map(str, error.absolute_path)) or '<root>'}: {error.message}"
              for error in Draft202012Validator(schema).iter_errors(data)]
    if errors:
        return errors
    for service_id, service in data["provides"].items():
        if service["port"] not in data["ports"]:
            errors.append(f"provides.{service_id}.port must be declared in ports")
    if errors:
        return errors
    application = data.get("application")
    if application is None:
        return []
    limits = application["limits"]
    if limits["maxToolSeconds"] > limits["maxRunSeconds"]:
        errors.append("application.limits.maxToolSeconds must not exceed maxRunSeconds")
    state = application["state"]
    if "bindingRef" in state and state["bindingRef"] not in application["bindings"]:
        errors.append("application.state.bindingRef must name an application.bindings key")
    hooks = application.get("hooks", {})
    seen = set()
    for phase, entries in hooks.items():
        for hook in entries:
            if hook["id"] in seen:
                errors.append(f"application.hooks: duplicate hook id {hook['id']!r}")
            seen.add(hook["id"])
    if template_dir is None:
        return errors
    root = template_dir.resolve()
    deployment = application["deployment"]
    sources = [(f"deployment.{key}", deployment[key], False)
               for key in ("project", "toolchainLock") if key in deployment]
    sources.extend((f"hooks.{phase}.{hook['id']}.cwd", hook["cwd"], True)
                   for phase, entries in hooks.items() for hook in entries)
    for label, source, directory in sources:
        try:
            path = (root / source).resolve()
        except (OSError, RuntimeError):
            errors.append(f"application.{label}: cannot resolve source path")
            continue
        if not path.is_relative_to(root):
            errors.append(f"application.{label}: source must stay inside the template directory")
        elif (directory and not path.is_dir()) or (not directory and not path.is_file()):
            errors.append(f"application.{label}: referenced {'directory' if directory else 'file'} does not exist")
    return errors
