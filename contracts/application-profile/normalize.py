"""Pure profile expansion; consumers must validate the expanded manifest."""
from copy import deepcopy
from typing import Any


def application_profile(manifest: dict[str, Any]) -> Any:
    app = manifest.get("application")
    deployment = app.get("deployment") if isinstance(app, dict) else None
    return deployment.get("profile") if isinstance(deployment, dict) else None


def _fill(target: Any, defaults: dict[str, Any]) -> None:
    if not isinstance(target, dict):
        return
    for key, value in defaults.items():
        if key not in target:
            target[key] = deepcopy(value)
        elif isinstance(value, dict):
            _fill(target[key], value)


def normalize_application_profile(manifest: dict[str, Any], catalog: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(manifest)
    app = result.get("application")
    deployment = app.get("deployment") if isinstance(app, dict) else None
    if not isinstance(deployment, dict) or "profile" not in deployment:
        return result
    profile = application_profile(manifest)
    if not isinstance(profile, str) or profile not in catalog["profiles"]:
        raise ValueError(f"Unsupported application deployment profile: {profile}")
    contract = catalog["profiles"][profile]
    _fill(app, contract["defaults"])
    bindings = app.get("bindings")
    if isinstance(bindings, dict):
        for role, defaults in contract["bindings"].items():
            section = app.get("state") if role == "state" else deployment
            name = (section.get("bindingRef" if role == "state" else "ingressBindingRef")
                    if isinstance(section, dict) else None) if role in ("state", "ingress") else role
            if isinstance(name, str) and name in bindings:
                _fill(bindings[name], defaults)
    return result
