"""Pure v1 admission/defaulting; expressions are evaluated only by native Devs."""

from __future__ import annotations

import inspect
import json
import math
import re
from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
from typing import Any

DEFAULT_CONTRACT = json.loads(Path(__file__).with_name("contract.json").read_text())
Validator = Callable[[Any], Any]
MAX_YAML_BYTES = 1024 * 1024


def _fail(path: str, message: str) -> None:
    raise ValueError(f"Template v1 {path}: {message}")


def _expression(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("${") and value.endswith("}")


def _finite(value: Any, path: str = "/") -> None:
    if value is not None and not isinstance(value, (str, bool, int, float, list, dict)):
        _fail(path, "expected an interoperable JSON value")
    if (
        isinstance(value, int)
        and not isinstance(value, bool)
        and abs(value) > 9007199254740991
    ) or (
        isinstance(value, float)
        and (
            not math.isfinite(value)
            or (value.is_integer() and abs(value) > 9007199254740991)
        )
    ):
        _fail(path, "expected a finite interoperable JSON number")
    if isinstance(value, list):
        for index, item in enumerate(value):
            _finite(item, f"{path}/{index}")
    elif isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                _fail(path, "expected string JSON object keys")
            _finite(item, f"{'' if path == '/' else path}/{key}")


def parse_yaml_v1(source: str | bytes) -> Any:
    """Read bounded JSON-compatible YAML1.2 Core; no files, env or expression evaluation."""
    if not isinstance(source, (str, bytes)):
        raise TypeError("Template v1 /: expected YAML UTF-8 text or bytes")
    try:
        data = source.encode("utf-8", "strict") if isinstance(source, str) else source
        text = data.decode("utf-8", "strict")
    except UnicodeError:
        raise ValueError("Template v1 /: YAML must contain valid UTF-8") from None
    if len(data) > MAX_YAML_BYTES:
        _fail("/", "YAML exceeds 1 MiB")
    if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", text):
        _fail("/", "YAML contains unsupported control characters")

    # Library Core rules own scalar resolution; SafeLoader's YAML1.1 rules are
    # never changed globally. The subclass enforces only this source policy.
    from yaml.nodes import ScalarNode
    from yaml.tokens import AliasToken, DirectiveToken
    from yamlcore import CoreLoader

    class SourceLoader(CoreLoader):
        def get_token(self):
            token = super().get_token()
            if isinstance(token, AliasToken):
                raise TypeError("aliases are unsupported")
            if isinstance(token, DirectiveToken) and (
                token.name not in {"YAML", "TAG"}
                or (token.name == "YAML" and token.value != (1, 2))
            ):
                raise ValueError("only YAML1.2 directives are supported")
            return token

        def construct_object(self, node, deep=False):
            if (
                isinstance(node, ScalarNode)
                and node.tag
                in {
                    "tag:yaml.org,2002:bool",
                    "tag:yaml.org,2002:int",
                    "tag:yaml.org,2002:float",
                    "tag:yaml.org,2002:null",
                }
                and self.resolve(ScalarNode, node.value, (True, False)) != node.tag
            ):
                raise ValueError("explicit scalar tags cannot change the Core kind")
            return super().construct_object(node, deep=deep)

    loader = None
    try:
        loader = SourceLoader(text)
        value = loader.get_single_data()
        _finite(value)
        # Also reject invalid Unicode produced by escaped lone surrogate values.
        json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8", "strict")
        return value
    except Exception:  # noqa: BLE001 - Parser errors contain source lines/values.
        raise ValueError(
            "Template v1 /: invalid JSON-compatible YAML1.2 Core: use one document "
            "with string keys; duplicate keys, aliases, unsupported tags and unsafe "
            "values are not allowed"
        ) from None
    finally:
        if loader is not None:
            loader.dispose()


def _checked(value: Any, validate: Validator) -> None:
    if not callable(validate):
        raise TypeError(
            "Pass an actual schema validator for the selected validation stage"
        )
    try:
        result = validate(value)
        if inspect.isawaitable(result):
            if hasattr(result, "close"):
                result.close()
            _fail("/", "use a synchronous schema validator")
        if result is False:
            _fail("/", "schema validation failed")
    except Exception as error:
        if isinstance(error, ValueError) and str(error).startswith("Template v1 "):
            raise error from None
        path = "/" + "/".join(str(key) for key in getattr(error, "path", []))
        raise ValueError(f"Template v1 {path}: schema validation failed") from None


def _fill(target: dict[str, Any], values: dict[str, Any]) -> None:
    for key, value in values.items():
        if key not in target:
            target[key] = deepcopy(value)
        elif isinstance(value, dict) and isinstance(target[key], dict):
            _fill(target[key], value)


def schema_for_stage(schema: dict[str, Any], stage: str = 'intent') -> dict[str, Any]:
    """Return shape validation for intent or expression-resolved inputs."""
    if stage not in {'intent', 'resolved'}:
        raise ValueError('Unknown template validation stage')
    def strip(value):
        if isinstance(value, list):
            return [strip(item) for item in value]
        if not isinstance(value, dict):
            return value
        if stage == 'resolved' and isinstance(value.get('oneOf'), list) and value['oneOf'][-1].get('$ref') == '#/$defs/expression':
            return strip(value['oneOf'][0])
        return {key: strip(item) for key, item in value.items()}
    return strip(deepcopy(schema))


def _local_path(value: str, path: str) -> None:
    if _expression(value):
        return
    if value.startswith('/') or re.match(r'^[A-Za-z]:', value) or '\\' in value or '\0' in value or '..' in value.split('/'):
        _fail(path, 'expected a relative path contained in the template directory')


def _references(value: Any) -> set[str]:
    if isinstance(value, str):
        return set(re.findall(r'\$\{resources\.([A-Za-z][A-Za-z0-9_-]*)\.output(?:\.[^}]+)?\}', value))
    if isinstance(value, dict):
        value = list(value.values())
    return set().union(*(_references(item) for item in value)) if isinstance(value, list) else set()


def normalize_template_v1(manifest: dict[str, Any], validate: Validator, *, stage: str = 'intent', contract: dict[str, Any] = DEFAULT_CONTRACT, provider: str | None = None, validate_provider: Callable[[str, Any, str], Any] | None = None) -> dict[str, Any]:
    """Validate named resources without credentials, runtime defaults or expression evaluation."""
    if stage not in {'intent', 'resolved'}:
        raise ValueError('Unknown template validation stage')
    _finite(manifest)
    result = deepcopy(manifest)
    _checked(result, validate)
    all_resources = {**result.get('sandbox', {}), **result.get('serving', {})}
    for name in result.get('sandbox', {}):
        if name in result.get('serving', {}):
            _fail('/sandbox/' + name, 'resource names must be globally unique')
    for name, resource in result.get('sandbox', {}).items():
        path, template = '/sandbox/' + name, resource['template']
        if provider and provider != resource['provider']:
            _fail(path + '/provider', 'conflicts with selected Provider context')
        if template.get('reference') and set(template) - {'reference', 'region'}:
            _fail(path + '/template', 'a borrowed template accepts only reference and region')
        build = template.get('buildConfig', {})
        if build.get('dockerfile'):
            _local_path(build['dockerfile'], path + '/template/buildConfig/dockerfile')
            if 'context' not in build and not _expression(build['dockerfile']):
                build['context'] = '/'.join(build['dockerfile'].split('/')[:-1]) or '.'
            if 'context' in build:
                _local_path(build['context'], path + '/template/buildConfig/context')
        if build.get('steps'):
            if not template.get('image'):
                _fail(path + '/template/image', 'steps require an input image')
            for index, step in enumerate(build['steps']):
                count = len(step['args'])
                where = path + '/template/buildConfig/steps/' + str(index)
                if step['type'] == 'ENV' and count % 2:
                    _fail(where, 'ENV requires key/value pairs')
                if step['type'] == 'WORKDIR' and count != 1 or step['type'] in {'USER', 'RUN'} and count > 2:
                    _fail(where, 'invalid step argument count')
                if step['type'] == 'USER' and count == 2 and step['args'][1] not in {'true', 'false'}:
                    _fail(where, 'USER sudo must be a boolean string')
        for volume_name, volume in resource.get('volumes', {}).items():
            if resource['provider'] == 'alicloud-express' and 'props' in volume:
                storage = {'agenticBucketVolumeConfig', 'agenticFSVolumeConfig', 'juiceFSVolumeConfig', 'ossVolumeConfig'}
                if len(storage & set(volume['props'])) != 1:
                    _fail(path + '/volumes/' + volume_name + '/props', 'choose exactly one storage backend')
                if set(volume['props']) - storage - {'mountConfig', 'volumeName'}:
                    _fail(path + '/volumes/' + volume_name + '/props', 'unsupported Express volume creation field')
        if stage == 'resolved' and validate_provider:
            def invoke(operation, value, where):
                try:
                    accepted = validate_provider(operation, deepcopy(value), resource['provider'])
                    if inspect.isawaitable(accepted):
                        if hasattr(accepted, 'close'): accepted.close()
                        _fail(where, 'selected Provider validation failed')
                    if accepted is False:
                        _fail(where, 'selected Provider validation failed')
                except Exception:
                    raise ValueError(f'Template v1 {where}: selected Provider validation failed') from None
            if not template.get('reference'):
                invoke('template.prepare', template, path + '/template')
            for volume_name, volume in resource.get('volumes', {}).items():
                if 'props' in volume:
                    invoke('volume.create', volume['props'], path + '/volumes/' + volume_name + '/props')
    dependencies = {}
    for name, resource in all_resources.items():
        actions = resource.get('actions', {})
        configuration = {key: value for key, value in resource.items() if key != 'actions'}
        required = _references([configuration, actions.get('pre-deploy')])
        after = _references([actions.get(key) for key in ['success-deploy', 'fail-deploy', 'complete-deploy']])
        dependencies[name] = required | (after - {name})
    if _references(result.get('vars', {})) - set(all_resources):
        _fail('/vars', 'resource output reference was not found')
    for name, names in dependencies.items():
        if names - set(all_resources):
            _fail('/resources/' + name, 'resource output reference was not found')
    visited, visiting = set(), set()
    def visit(name):
        if name in visiting:
            _fail('/resources/' + name, 'cyclic resource output dependency')
        if name in visited: return
        visiting.add(name)
        for dependency in dependencies[name]: visit(dependency)
        visiting.remove(name)
        visited.add(name)
    for name in dependencies: visit(name)
    _checked(result, validate)
    return result


def compile_template_v1(manifest: dict[str, Any], validate: Validator, *, stage: str = 'resolved', **options: Any) -> dict[str, Any]:
    """Compile resolved input without reconstructing retired application or instance recipes."""
    if stage != 'resolved':
        raise ValueError('Compile requires parser-resolved input')
    result = normalize_template_v1(manifest, validate, stage=stage, **options)
    result.pop('specVersion')
    result['kind'] = 'application' if result.get('sandbox') and result.get('serving') else 'serving' if result.get('serving') else 'sandbox'
    return result


def pointer_value(document: Any, pointer: str) -> Any:
    """Decode a non-root JSON Pointer without accepting stale/implicit paths."""
    if (
        not isinstance(pointer, str)
        or not pointer.startswith("/")
        or re.search(r"~(?![01])", pointer)
    ):
        _fail("/parameters/target", "expected a non-root JSON Pointer")
    value = document
    for encoded in pointer[1:].split("/"):
        key = encoded.replace("~1", "/").replace("~0", "~")
        if isinstance(value, list):
            if not re.fullmatch(r"0|[1-9][0-9]*", key) or int(key) >= len(value):
                _fail("/parameters/target", "target was not found")
            value = value[int(key)]
        else:
            if not isinstance(value, dict) or key not in value:
                _fail("/parameters/target", "target was not found")
            value = value[key]
    return deepcopy(value)


def normalize_registry_v1(
    metadata: dict[str, Any],
    template: dict[str, Any],
    validate_registry: Validator,
    validate_template: Validator,
    *,
    contract: dict[str, Any] = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    """Validate optional metadata; runtime normalization never reads it."""
    _finite(metadata)
    _checked(metadata, validate_registry)
    result = deepcopy(metadata)
    intent = normalize_template_v1(template, validate_template, contract=contract)
    _fill(result, {"entry": "template.yaml", "parameters": []})
    targets: set[str] = set()
    for index, parameter in enumerate(result["parameters"]):
        if parameter["target"] in targets:
            _fail(f"/parameters/{index}/target", "duplicate parameter target")
        targets.add(parameter["target"])
        value = pointer_value(intent, parameter["target"])
        if parameter.get("sensitive"):
            env = parameter["environmentVariable"]
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", env) or value not in (
                "${env('" + env + "')}",
                '${env("' + env + '")}',
            ):
                _fail(
                    f"/parameters/{index}/target",
                    "a sensitive parameter must target its declared native env expression",
                )
    return result
