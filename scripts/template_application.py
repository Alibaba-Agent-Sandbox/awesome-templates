"""Validate the v3 manifest without executing hooks, adapters, or cloud APIs."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schema" / "template-v3.schema.json"


def validate_v3(data: dict[str, Any], template_dir: Path | None = None) -> list[str]:
    """Return schema/semantic errors; optional source checks stay under the template root."""
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return ["v3 validation needs jsonschema==4.26.0; install scripts/requirements-spec.txt"]
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = [f"{'.'.join(map(str, error.absolute_path)) or '<root>'}: {error.message}"
              for error in Draft202012Validator(schema).iter_errors(data)]
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
