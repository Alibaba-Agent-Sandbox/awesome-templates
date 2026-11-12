"""Validate public v1 manifests and project private engineering inputs without execution."""

from __future__ import annotations

import importlib.util
import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml
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
    """Classify only the explicit business type, never the version or resource names."""
    return (
        isinstance(data.get("application"), dict)
        and data["application"].get("type") == "agents-api"
    )


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


def publication_metadata(
    template_dir: Path, data: dict[str, Any]
) -> dict[str, Any] | None:
    """Load optional author metadata; it is not used by runtime resource normalization."""
    path = template_dir / "registry.yaml"
    if not path.is_file():
        return None
    if path.is_symlink() or path.stat().st_size > 1024 * 1024:
        raise ValueError("publication metadata must be a bounded regular file")
    metadata = yaml.safe_load(path.read_text())
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


def project_manifest(
    data: dict[str, Any],
    template_dir: Path | None = None,
    *,
    provider: str | None = "alicloud-express",
) -> dict[str, Any]:
    """Project v1 into private legacy-shaped test inputs, not an executable public format.

    Expressions stay literal. Only the actual CLI native-parser consumer resolves them.
    Provider profile/image facts and publication metadata are derived from their own source.
    """
    normalized = normalize_manifest(
        data, provider if not data.get("sandbox", {}).get("provider") else None
    )
    sb = normalized.get("sandbox", {})
    template = sb.get("template", {})
    services = sb.get("services", {})
    result: dict[str, Any] = {
        "specVersion": 1,
        "name": normalized["name"],
        "sandbox": deepcopy(sb),
        "resources": deepcopy(template.get("props", {})),
        "env": deepcopy(sb.get("instance", {}).get("envs", {})),
        "provides": deepcopy(services),
        "ports": sorted(
            set(sb.get("ports", [])) | {v["port"] for v in services.values()}
        ),
        "start_cmd": sb.get("start"),
        "ready_cmd": sb.get("ready"),
        "provider": sb.get("provider"),
        **engineering_checks(
            "_skeleton"
            if template_dir is not None and template_dir.name == "_skeleton"
            else normalized["name"]
        ),
    }
    if "image" in template:
        result["image"] = template["image"]
    if "reference" in template:
        result["template_id"] = template["reference"]
    if "aliases" in template:
        result["aliases"] = deepcopy(template["aliases"])
    if template.get("source", {}).get("profiles"):
        result["build_profiles"] = deepcopy(template["source"]["profiles"])
    if template_dir is not None:
        metadata = publication_metadata(template_dir, data)
        if metadata:
            result.update(
                version=metadata["version"],
                description=metadata["description"]["en"],
                author=metadata["author"],
                license=metadata["license"],
                tags=metadata.get("tags", []),
            )
        recipe = template.get("source", {}).get("dockerfile", "Dockerfile")
        dockerfile = template_dir / recipe
        if dockerfile.is_file():
            match = re.search(
                r"(?im)^\s*FROM\s+(?:--platform=\S+\s+)?([^\s]+)",
                dockerfile.read_text(),
            )
            if match:
                result["base"] = match[1]
    if "deployment" in normalized:
        result["deployment"] = deepcopy(normalized["deployment"])
    if is_managed_application(normalized):
        app = normalized["application"]
        legacy = deepcopy(PROFILE_CATALOG["managedProfile"]["defaults"])
        legacy["type"] = "agents-api"
        legacy["sessions"].update(deepcopy(app["sessions"]))
        legacy["sessions"]["maxLifetimeSeconds"] = sb["instance"]["timeout"]
        legacy["limits"] = deepcopy(app["limits"])
        legacy["storage"].update(deepcopy(app["storage"]))
        legacy["sandbox"]["provider"] = sb["provider"]
        legacy["state"]["bindingRef"] = "state"
        legacy["bindings"] = {
            name: {"reference": name, **deepcopy(value)}
            for name, value in PROFILE_CATALOG["managedProfile"]["bindings"].items()
        }
        deployment = normalized["deployment"]
        role = deployment["resources"][app["roles"]["gateway"]]
        legacy["deployment"].update(
            profile="fc-managed-agents",
            accessRef=deployment["access"],
            component=role["component"],
            region=role["props"].get("region")
            if isinstance(role["props"], dict)
            else None,
            ingressBindingRef="ingress",
        )
        legacy["deployment"].update(
            serverBuildRecipe=deepcopy(app["server"]["source"])
        ) if "source" in app["server"] else legacy["deployment"].update(
            serverImage=app["server"]["image"]
        )
        if "hooks" in app:
            legacy["hooks"] = deepcopy(app["hooks"])
        result["application"] = legacy
    return result


def validate_manifest(
    data: dict[str, Any], template_dir: Path | None = None
) -> list[str]:
    """Admit only v1 and validate source/hook containment without adapters or cloud calls."""
    try:
        normalized = normalize_manifest(data)
        if template_dir is not None:
            sb = normalized.get("sandbox", {})
            recipes = []
            source = sb.get("template", {}).get("source")
            if source:
                recipes.append(source)
                recipes.extend(source.get("profiles", {}).values())
            app = normalized.get("application")
            if app and app["server"].get("source"):
                recipes.append(app["server"]["source"])
            for recipe in recipes:
                _contained(template_dir, recipe["dockerfile"])
                _contained(template_dir, recipe["context"], directory=True)
            if app:
                ids = set()
                for hooks in app.get("hooks", {}).values():
                    for hook in hooks:
                        if hook["id"] in ids:
                            raise ValueError("duplicate hook id")
                        ids.add(hook["id"])
                        if hook["type"] == "custom":
                            _contained(
                                template_dir, hook.get("cwd", "."), directory=True
                            )
            publication_metadata(template_dir, data)
        return []
    except (OSError, TypeError, ValueError) as error:
        return [str(error)]


def validate_v1(data: dict[str, Any], template_dir: Path | None = None) -> list[str]:
    """Explicit first-public-version validator."""
    return validate_manifest(data, template_dir)
