"""Validate public v1 manifests and project private engineering inputs without execution."""

from __future__ import annotations

import importlib.util
import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "spec/template-v1.schema.json"
REGISTRY_SCHEMA_PATH = ROOT / "spec/registry-v1.schema.json"
PROFILE_ROOT = ROOT / "contracts/template-v1"
_profile_spec = importlib.util.spec_from_file_location(
    "template_v1_contract", PROFILE_ROOT / "normalize.py"
)
assert _profile_spec and _profile_spec.loader
_profile_module = importlib.util.module_from_spec(_profile_spec)
_profile_spec.loader.exec_module(_profile_module)
PROFILE_CATALOG = json.loads((PROFILE_ROOT / "contract.json").read_text())
_VALIDATOR = Draft202012Validator(json.loads(SCHEMA_PATH.read_text())).validate
_REGISTRY_VALIDATOR = Draft202012Validator(
    json.loads(REGISTRY_SCHEMA_PATH.read_text())
).validate


def normalize_manifest(
    data: dict[str, Any], provider: str | None = None
) -> dict[str, Any]:
    """Return canonical v1 intent; this never evaluates native Devs expressions."""
    return _profile_module.normalize_template_v1(data, _VALIDATOR, provider=provider)


def is_managed_application(data: dict[str, Any]) -> bool:
    """Classify actual native Serving configuration for owner-specific engineering tests."""
    if data.get("application", {}).get("type") == "agents-api":
        return True  # Already projected engineering test input only.
    for resource in data.get("serving", {}).values():
        props = resource.get("props", {})
        env = props.get("environmentVariables", {})
        container = props.get("customContainerConfig", {})
        if not isinstance(env, dict) or not isinstance(container, dict):
            continue
        command = container.get("command", [])
        if {"ABX_MANAGED_DATABASE_URL", "AGENTS_POLICY_JSON"} <= set(env) and command in (["worker"], ["gateway"], ["dispatcher"]):
            return True
    return False


def _contained(root: Path, value: str, *, directory: bool = False) -> Path:
    path = root / value
    if (
        Path(value).is_absolute()
        or path.is_symlink()
        or not path.resolve().is_relative_to(root.resolve())
    ):
        raise ValueError("referenced source must stay inside the template directory")
    if not (path.is_dir() if directory else path.is_file()):
        raise ValueError("referenced source does not exist")
    return path


def load_source_document(path: Path) -> Any:
    """Read only the bounded v1 source profile, without native/config evaluation."""
    with path.open("rb") as stream:
        data = stream.read(_profile_module.MAX_YAML_BYTES + 1)
    return _profile_module.parse_yaml_v1(data)


def publication_metadata(
    template_dir: Path, data: dict[str, Any]
) -> dict[str, Any] | None:
    """Load optional author metadata; it is not used by runtime resource normalization."""
    path = template_dir / "registry.yaml"
    if not path.is_file():
        return None
    if path.is_symlink() or path.stat().st_size > 1024 * 1024:
        raise ValueError("publication metadata must be a bounded regular file")
    metadata = load_source_document(path)
    result = _profile_module.normalize_registry_v1(
        metadata, data, _REGISTRY_VALIDATOR, _VALIDATOR
    )
    for value in result["readme"].values():
        _contained(template_dir, value)
    return result


def engineering_checks(name: str) -> dict[str, Any]:
    """Read owned CI smoke declarations, never user runtime resource properties."""
    return deepcopy(
        json.loads((ROOT / "scripts/template-checks.json").read_text())[
            "templates"
        ].get(name, {})
    )


def _image_environment(dockerfile: Path) -> dict[str, str]:
    import shlex
    if not dockerfile.is_file():
        return {}
    env: dict[str, str] = {}
    text = dockerfile.read_text().replace("\\\n", " ")
    for line in text.splitlines():
        if line.lstrip().startswith("ENV "):
            for token in shlex.split(line.strip()[4:]):
                if "=" in token:
                    key, value = token.split("=", 1)
                    env[key] = value
    return env


def project_manifest(data: dict[str, Any], template_dir: Path | None = None, *, provider: str | None = None) -> dict[str, Any]:
    """Project current resources into engineering smoke inputs; never runtime configuration."""
    normalized = normalize_manifest(data)
    entries = list(normalized.get("sandbox", {}).values())
    if len(entries) != 1:
        raise ValueError("the template smoke runner requires exactly one sandbox resource")
    sb = entries[0]
    template = sb["template"]
    name = "_skeleton" if template_dir is not None and template_dir.name == "_skeleton" else normalized["name"]
    checks = engineering_checks(name)
    if is_managed_application(normalized):
        managed_checks = engineering_checks("agents-api")
        checks = {**managed_checks, **checks}
        checks["localRuntime"] = managed_checks.get("localRuntime", {})
    services = checks.get("services", {})
    runtime = checks.get("runtime", checks.get("localRuntime", {}))
    result: dict[str, Any] = {
        "specVersion": 1, "name": normalized["name"], "sandbox": deepcopy(sb),
        "resources": {"cpu": template.get("cpu"), "memory": template.get("memorySize")},
        "env": {}, "provides": deepcopy(services),
        "ports": sorted(set(checks.get("ports", [])) | {v["port"] for v in services.values()}),
        "start_cmd": template.get("startCommand", runtime.get("start")), "ready_cmd": template.get("readyCommand", runtime.get("ready")),
        "provider": sb["provider"], **{k: v for k, v in checks.items() if k in {"smoke", "priority", "wave"}},
    }
    if "image" in template: result["image"] = template["image"]
    if "reference" in template: result["template_id"] = template["reference"]
    if checks.get("alternativeRecipes"): result["build_profiles"] = deepcopy(checks["alternativeRecipes"])
    if template_dir is not None:
        metadata = publication_metadata(template_dir, data)
        if metadata:
            result.update(version=metadata["version"], description=metadata["description"]["en"], author=metadata["author"], license=metadata["license"], tags=metadata.get("tags", []))
        dockerfile = template_dir / template.get("buildConfig", {}).get("dockerfile", "Dockerfile")
        if dockerfile.is_file():
            result["env"] = _image_environment(dockerfile)
            text = dockerfile.read_text()
            match = re.search(r"(?im)^\s*FROM\s+(?:--platform=\S+\s+)?([^\s]+)", text)
            if match: result["base"] = match[1]
            for line in text.splitlines():
                if line.startswith("EXPOSE "):
                    result["ports"] = sorted(set(result["ports"]) | {int(port.split("/")[0]) for port in line.split()[1:] if port.split("/")[0].isdigit()})
    if is_managed_application(normalized):
        result["application"] = {"type": "agents-api"}  # Engineering runner classification only.
    if "serving" in normalized: result["serving"] = deepcopy(normalized["serving"])
    return result


def validate_manifest(data: dict[str, Any], template_dir: Path | None = None) -> list[str]:
    """Validate all named resources and contained local paths without executing actions."""
    try:
        normalized = normalize_manifest(data)
        if template_dir is not None:
            for resource in normalized.get("sandbox", {}).values():
                build = resource["template"].get("buildConfig", {})
                if "dockerfile" in build and not build["dockerfile"].startswith("${"):
                    _contained(template_dir, build["dockerfile"])
                    if not build.get("context", ".").startswith("${"):
                        _contained(template_dir, build.get("context", "."), directory=True)
            for resource in list(normalized.get("sandbox", {}).values()) + list(normalized.get("serving", {}).values()):
                for actions in resource.get("actions", {}).values():
                    for action in actions:
                        if action.get("path") and not action["path"].startswith("${"):
                            _contained(template_dir, action["path"], directory=True)
            publication_metadata(template_dir, data)
        return []
    except (OSError, TypeError, ValueError, RuntimeError) as error:
        return [str(error)]


def validate_v1(data: dict[str, Any], template_dir: Path | None = None) -> list[str]:
    return validate_manifest(data, template_dir)
