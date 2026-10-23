"""Validate the v4 manifest without executing hooks, adapters, or cloud APIs."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "spec" / "template-v4.schema.json"


def validate_workflow_references(data: dict[str, Any]) -> list[str]:
    """Check references after schema validation for either source or managed inputs."""
    errors = []
    workflows = data["workflows"]
    if data["default_workflow"] not in workflows:
        errors.append("default_workflow must name an existing workflow")
    for workflow_id, workflow in workflows.items():
        if workflow["kind"] == "application":
            service = data["provides"].get(workflow["service"])
            if service is None:
                errors.append(f"workflows.{workflow_id}.service must name a declared provided service")
            elif workflow["operation"] not in service["operations"]:
                errors.append(f"workflows.{workflow_id}.operation is not provided by the selected service")
        elif "service" in workflow:
            errors.append(f"workflows.{workflow_id}: service only applies to application workflows")
        if workflow["startup"] == "exec" and not data.get("start_cmd", "").strip():
            errors.append(f"workflows.{workflow_id}: exec startup needs an explicit start_cmd")
    return errors


def validate_v4(data: dict[str, Any], template_dir: Path | None = None) -> list[str]:
    """Return schema/semantic errors; optional source checks stay under the template root."""
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return ["v4 validation needs jsonschema==4.26.0; install scripts/requirements-spec.txt"]
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = [f"{'.'.join(map(str, error.absolute_path)) or '<root>'}: {error.message}"
              for error in Draft202012Validator(schema).iter_errors(data)]
    if errors:
        return errors
    errors.extend(validate_workflow_references(data))
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
