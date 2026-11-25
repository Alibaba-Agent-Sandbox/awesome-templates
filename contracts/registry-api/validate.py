"""Package-local API publication checks; invocation remains the CLI's responsibility."""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path
from urllib.parse import unquote

_reader_spec = importlib.util.spec_from_file_location(
    "registry_api_yaml_reader", Path(__file__).parents[1] / "template-v1" / "normalize.py"
)
_reader = importlib.util.module_from_spec(_reader_spec)
_reader_spec.loader.exec_module(_reader)
MAX_BYTES = 1024 * 1024
METHODS = {"get", "put", "post", "delete", "options", "head", "patch"}
MAPS = {"properties", "patternProperties", "$defs", "dependentSchemas", "schemas",
        "securitySchemes", "parameters", "requestBodies", "paths", "content",
        "responses", "headers", "callbacks", "webhooks"}


def _read(path: Path) -> dict:
    if not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise ValueError("Registry and OpenAPI files must be regular files no larger than 1 MiB")
    value = _reader.parse_yaml_v1(path.read_bytes())
    count = 0

    def visit(item, depth=0):
        nonlocal count
        count += 1
        if count > 20000 or depth > 48:
            raise ValueError("API contract exceeds the supported complexity limit")
        if isinstance(item, dict):
            for key, child in item.items():
                if key in {"__proto__", "prototype", "constructor"}:
                    raise ValueError("API contract contains an unsupported object key")
                visit(child, depth + 1)
        elif isinstance(item, list):
            for child in item:
                visit(child, depth + 1)

    visit(value)
    if not isinstance(value, dict):
        raise ValueError("Registry and OpenAPI documents must be objects")
    if len(json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode()) > MAX_BYTES:
        raise ValueError("Normalized API contract exceeds 1 MiB")
    return value


def _pointer(document: dict, ref):
    if not isinstance(ref, str) or not ref.startswith("#/"):
        raise ValueError("Bundle external OpenAPI references before publishing")
    if re.search(r"%(?![a-fA-F0-9]{2})", ref):
        raise ValueError("Invalid OpenAPI reference encoding")
    value = document
    for key in unquote(ref[2:], errors="strict").split("/"):
        if re.search(r"~(?:[^01]|$)", key):
            raise ValueError("Invalid OpenAPI JSON Pointer escape")
        key = key.replace("~1", "/").replace("~0", "~")
        if isinstance(value, list) and re.fullmatch(r"0|[1-9][0-9]*", key):
            if int(key) >= len(value):
                raise ValueError("OpenAPI reference does not exist")
            value = value[int(key)]
        elif isinstance(value, dict) and key in value:
            value = value[key]
        else:
            raise ValueError("OpenAPI reference does not exist")
    return value


def _check_references(document: dict):
    active, done = set(), set()

    def visit(value, is_map=False):
        if not isinstance(value, (dict, list)):
            return
        identity = id(value)
        if identity in active:
            raise ValueError("Recursive OpenAPI references are not supported")
        if identity in done:
            return
        active.add(identity)
        if isinstance(value, dict):
            if not is_map and "$ref" in value:
                visit(_pointer(document, value["$ref"]))
            for key, child in value.items():
                if not is_map and key.startswith("x-abx-"):
                    raise ValueError("x-abx invocation extensions are not supported")
                if not is_map and key in {"example", "examples", "default", "enum", "const"}:
                    continue
                visit(child, not is_map and key in MAPS)
        else:
            for child in value:
                visit(child)
        active.remove(identity)
        done.add(identity)

    visit(document)


def read_api_bindings(package: Path) -> list[dict]:
    """Return a small, non-secret catalog summary, never endpoint/auth/default values.

    This validates only optional API metadata. It does not activate the proposed
    Registry publication envelope or the named-resource deployment engine.
    """
    root = package.resolve()
    registry_file = root / "registry.yaml"
    if not registry_file.exists():
        return []
    if not registry_file.resolve().is_relative_to(root):
        raise ValueError("Registry file escapes its package directory")
    registry = _read(registry_file)
    if "apis" not in registry:
        return []
    entries = registry["apis"]
    if not isinstance(entries, dict) or not 1 <= len(entries) <= 32:
        raise ValueError("registry.apis must contain between 1 and 32 APIs")
    summaries = []
    for name, entry in entries.items():
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,63}", name):
            raise ValueError("Invalid Registry API name")
        if not isinstance(entry, dict) or set(entry) != {"resource", "port", "openapi"}:
            raise ValueError("Registry API entries require resource, port and openapi only")
        if not isinstance(entry["resource"], str) or not re.fullmatch(r"sandbox\.[A-Za-z][A-Za-z0-9_-]*", entry["resource"]):
            raise ValueError("Registry API binding requires a sandbox.NAME resource")
        if type(entry["port"]) is not int or not 1 <= entry["port"] <= 65535:
            raise ValueError("Registry API port must be an integer between 1 and 65535")
        source = entry["openapi"]
        if not isinstance(source, str) or Path(source).is_absolute() or re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", source):
            raise ValueError("Registry OpenAPI must reference a package-local file")
        path = (root / source).resolve()
        if not path.is_relative_to(root):
            raise ValueError("Registry OpenAPI file escapes its package directory")
        document = _read(path)
        if not isinstance(document.get("openapi"), str) or not re.fullmatch(r"3\.1\.\d+", document["openapi"]):
            raise ValueError("Registry API binding supports OpenAPI 3.1 only")
        _check_references(document)
        if not isinstance(document.get("paths"), dict):
            raise ValueError("OpenAPI paths must be an object")
        operations, identifiers = [], set()
        for route, item in document["paths"].items():
            if route.startswith("x-"):
                continue
            if not route.startswith("/") or route.startswith("//") or re.search(r"[?#\\\x00-\x20]", route):
                raise ValueError("OpenAPI operation path must be a relative HTTP path")
            while isinstance(item, dict) and "$ref" in item:
                if set(item) - {"$ref", "summary", "description"}:
                    raise ValueError("Unsupported OpenAPI Reference Object siblings")
                item = _pointer(document, item["$ref"])
            if not isinstance(item, dict):
                raise ValueError("OpenAPI path item must be an object")
            if "trace" in item:
                raise ValueError("TRACE operations are not supported")
            for method, operation in item.items():
                if method not in METHODS:
                    continue
                if not isinstance(operation, dict):
                    raise ValueError("OpenAPI operation must be an object")
                if "operationId" not in operation:
                    continue
                identifier = operation["operationId"]
                if not isinstance(identifier, str) or not identifier or re.search(r"[\s\x00-\x1f]", identifier) or identifier.startswith("-"):
                    raise ValueError("Invalid OpenAPI operationId")
                if identifier in identifiers:
                    raise ValueError("OpenAPI operationId must be unique within an API")
                identifiers.add(identifier)
                operations.append({"operationId": identifier, "method": method.upper(), "path": route})
        if not operations:
            raise ValueError("OpenAPI document has no callable operationId")
        summaries.append({"name": name, **entry, "operations": operations})
    return summaries
