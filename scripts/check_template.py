#!/usr/bin/env python3
"""Lint one template directory against docs/template-spec.md.

Exit status:
  0  the directory conforms, or ``--all`` found no supported-spec failures
  1  at least one violation in a directory that claims a supported spec version
     (``--all`` still prints the legacy conformance list)

A directory without ``spec_version`` is legacy. Versions 2 and 3 are supported.
An unknown explicit version is a claimed spec failure. ``--all`` ignores only
legacy violations; ``--strict`` fails on every violation.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - CI installs PyYAML
    print("check_template.py needs PyYAML (pip install pyyaml)", file=sys.stderr)
    raise SystemExit(1)

ROOT = Path(__file__).resolve().parents[1]

README_EN = (
    "What it does",
    "Stack",
    "Problem solved",
    "Quick start (CLI)",
    "Quick start (Python SDK)",
    "Quick start (HTTP POST)",
    "Command reference",
    "Configuration",
    "Resources",
    "Verified",
    "Secondary development",
    "Contributing",
    "Issues",
    "License",
)
README_ZH = (
    "做什么",
    "技术栈",
    "解决的问题",
    "快速开始（CLI）",
    "快速开始（Python SDK）",
    "快速开始（HTTP POST）",
    "命令参考",
    "配置",
    "资源",
    "已验证",
    "二次开发",
    "贡献",
    "问题反馈",
    "许可证",
)
DESIGN_HEADINGS = (
    "Purpose",
    "Capabilities",
    "Exposed API",
    "How to build",
    "Express feasibility",
    "Risks",
    "Test plan",
)
# Allowed agent-sandbox-server installs. Either form on a RUN line is a pin.
# PyPI:  agent-sandbox-server==X.Y.Z
# git:   agent-sandbox-server @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/<40-hex>.tar.gz#subdirectory=server-sdk
SERVER_PYPI_PIN = re.compile(
    r"agent-sandbox-server==([0-9]+\.[0-9]+\.[0-9]+(?:[A-Za-z0-9.+-]*)?)"
)
SERVER_GIT_ARCHIVE = re.compile(
    r"agent-sandbox-server\s*@\s*[\"']?"
    r"https://github\.com/Alibaba-Agent-Sandbox/python-sdk/archive/"
    r"([0-9a-fA-F]{40})\.tar\.gz#subdirectory=server-sdk"
)
# `pip install agent-sandbox` is a different project. `-client` and `-server` are ours.
BARE_CLIENT_INSTALL = re.compile(
    r"\bpip(?:3)?\s+install\b[^\n]*?(?:\s|['\"=])agent-sandbox(?![\w.-])"
)
FC_PLACEHOLDER = "fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>"
FC_PINNED = re.compile(
    r"^fc-e2b-registry\.[a-z0-9-]+\.cr\.aliyuncs\.com/runtime/base:v\d+\.\d+\.\d+$"
)
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
SECRET_KEY = re.compile(
    r"(^|_)(API_KEY|SECRET|TOKEN|PASSWORD|CREDENTIAL|PRIVATE_KEY)$",
    re.IGNORECASE,
)
PROVIDERS = {
    "alicloud-express": ("express", "alicloud-express"),
    "alicloud-container": ("alicloud-container",),
    "cubesandbox": ("cubesandbox",),
    "e2b": ("e2b",),
    "opensandbox": ("opensandbox",),
}
EMPTY_VERIFIED = (
    "No provider has a passing run recorded for this template.",
    "尚未记录任何通过的提供方测试。",
)
REQUIRED_FILES = (
    "template.yaml",
    "Dockerfile",
    "commands.py",
    "e2e_test.py",
    "README.md",
    "README.zh-CN.md",
)
SKELETON_NAME = "_skeleton"


@dataclass(frozen=True)
class Violation:
    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


class _UniqueKeyLoader(yaml.SafeLoader):
    """Reject ambiguous maps instead of silently accepting the final key."""


def _unique_mapping(loader: yaml.SafeLoader, node: yaml.MappingNode, deep: bool = False) -> dict:
    loader.flatten_mapping(node)
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ValueError(f"duplicate YAML key {key!r}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


_UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _unique_mapping)


def _load_yaml(path: Path) -> tuple[object, list[Violation]]:
    try:
        data = yaml.load(path.read_text(encoding="utf-8"), Loader=_UniqueKeyLoader)
    except Exception as exc:  # noqa: BLE001 - surface the parser error
        return None, [Violation("yaml-parse", f"{path.name}: {exc}")]
    if not isinstance(data, dict):
        return None, [Violation("yaml-parse", f"{path.name} must be a mapping")]
    return data, []


def _sections(text: str) -> dict[str, str]:
    found: dict[str, str] = {}
    current: str | None = None
    body: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            if current is not None:
                found[current] = "\n".join(body).strip()
            current = line[3:].strip()
            body = []
        elif current is not None:
            body.append(line)
    if current is not None:
        found[current] = "\n".join(body).strip()
    return found


def _dockerfile_lines(text: str) -> list[str]:
    logical: list[str] = []
    buf = ""
    for raw in text.splitlines():
        stripped = raw.strip()
        if not buf and (not stripped or stripped.startswith("#")):
            continue
        if stripped.endswith("\\"):
            buf += stripped[:-1].strip() + " "
            continue
        buf += stripped
        if buf.strip():
            logical.append(buf.strip())
        buf = ""
    if buf.strip():
        logical.append(buf.strip())
    return logical


def _instruction(line: str) -> str:
    return line.split(None, 1)[0].upper()


def _server_sdk_pinned(line: str) -> bool:
    return SERVER_PYPI_PIN.search(line) is not None or SERVER_GIT_ARCHIVE.search(line) is not None


def _bad_client_install(text: str) -> bool:
    """True when a README tells the reader to pip-install the unrelated `agent-sandbox` project.

    A line that says that name is unrelated is the warning itself, not an install instruction.
    """
    for line in text.splitlines():
        lowered = line.lower()
        if "unrelated" in lowered or "无关" in line:
            continue
        if BARE_CLIENT_INSTALL.search(line):
            return True
    return False


def _from_image(line: str) -> str:
    parts = line.split()
    # FROM [--platform=...] image
    image = parts[-1]
    return image


def _providers_in(text: str) -> set[str]:
    found: set[str] = set()
    for provider in PROVIDERS:
        if re.search(rf"(?<![A-Za-z0-9-]){re.escape(provider)}(?![A-Za-z0-9-])", text):
            found.add(provider)
    return found


def _evidence_passes(template_dir: Path, provider: str) -> bool:
    evidence = template_dir / "evidence"
    if not evidence.is_dir():
        return False
    metadata, errors = _load_yaml(template_dir / "template.yaml")
    if errors or not isinstance(metadata, dict):
        return False
    slugs = PROVIDERS[provider]
    for path in sorted(evidence.glob("*.json")):
        matched = False
        for slug in slugs:
            prefix = f"{slug}-"
            if path.name.startswith(prefix) and path.suffix == ".json":
                date = path.name[len(prefix) : -len(".json")]
                if re.fullmatch(r"\d{4}-\d{2}-\d{2}(?:T\d{6}Z)?", date):
                    matched = True
                    break
        if not matched:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        if payload.get("provider") != provider or payload.get("passed") is not True or payload.get("cleanup_verified") is not True:
            continue
        if payload.get("template") != metadata.get("name") or str(payload.get("template_version")) != str(metadata.get("version")):
            continue
        commands = payload.get("commands")
        if not isinstance(commands, list) or not commands:
            continue
        vias = set()
        good = True
        for item in commands:
            if not isinstance(item, dict) or item.get("ok") is not True:
                good = False
                break
            via = item.get("via")
            if via in {"cli", "sdk"}:
                vias.add(via)
        if good and vias == {"cli", "sdk"}:
            return True
    return False


def _index_entries(root: Path) -> list[dict] | None:
    path = root / "awesome-templates.yaml"
    if not path.is_file():
        return None
    data, errors = _load_yaml(path)
    if errors or not isinstance(data, dict):
        return []
    templates = data.get("templates")
    if not isinstance(templates, list):
        return []
    return [item for item in templates if isinstance(item, dict)]


def _check_readme(path: Path, headings: tuple[str, ...], violations: list[Violation]) -> dict[str, str]:
    if not path.is_file():
        return {}
    sections = _sections(path.read_text(encoding="utf-8"))
    for heading in headings:
        if heading not in sections:
            violations.append(Violation("readme-section", f"{path.name}: missing section '## {heading}'"))
            continue
        if len(sections[heading].strip()) < 3:
            violations.append(Violation("readme-section", f"{path.name}: section '## {heading}' is empty"))
    english = "Command reference" in headings
    cli_heading = "Quick start (CLI)" if english else "快速开始（CLI）"
    sdk_heading = "Quick start (Python SDK)" if english else "快速开始（Python SDK）"
    commands_heading = "Command reference" if english else "命令参考"
    issues_heading = "Issues" if english else "问题反馈"
    cli = sections.get(cli_heading, "")
    sdk = sections.get(sdk_heading, "")
    commands = sections.get(commands_heading, "")
    issues = sections.get(issues_heading, "")
    if cli_heading in sections and "abx run" not in cli:
        violations.append(Violation("readme-cli", f"{path.name}: Quick start (CLI) must show `abx run`"))
    if sdk_heading in sections and ("Sandbox" not in sdk or ".run" not in sdk):
        violations.append(
            Violation("readme-sdk", f"{path.name}: Quick start (Python SDK) must show Sandbox and .run")
        )
    if commands_heading in sections and not any(line.strip().startswith("|") for line in commands.splitlines()):
        violations.append(Violation("readme-api", f"{path.name}: Command reference needs a parameter table"))
    for repo in ("awesome-templates", "python-sdk", "agent-sandbox"):
        if issues_heading in sections and repo not in issues:
            violations.append(Violation("readme-issues", f"{path.name}: Issues must name {repo}"))
    return sections


def _pip_hash_lock(line: str, template_dir: Path, docker_lines: list[str]) -> bool:
    """Recognize a fully pinned SHA256 file installed with pip hash enforcement.

    Limit this form to one plain local COPY mapping and no extra requirements.
    Other COPY/requirements syntaxes still need an independently supported pin.
    pip verifies dependency completeness and actual hashes during image build.
    """
    match = re.search(r"\bpip install\b([^&|;]*)", line)
    if not match:
        return False
    try:
        tokens = shlex.split(match[1])
    except ValueError:
        return False
    if tokens.count("-r") != 1 or "--require-hashes" not in tokens:
        return False
    index = tokens.index("-r")
    if index + 1 >= len(tokens):
        return False
    target = tokens[index + 1]
    remaining = tokens[:index] + tokens[index + 2:]
    if any(token not in {"--require-hashes", "--no-cache-dir", "--no-deps"} for token in remaining):
        return False
    sources = []
    for instruction in docker_lines:
        copied = re.fullmatch(r"COPY\s+([A-Za-z0-9_.-]+)\s+" + re.escape(target), instruction.strip())
        if copied:
            sources.append(copied[1])
    if len(sources) != 1 or sources[0] in {".", ".."}:
        return False
    path = template_dir / sources[0]
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 2 * 1024**2:
        return False
    entries = []
    pending = ""
    for raw in path.read_text(encoding="utf-8").splitlines():
        value = raw.strip()
        if not value or value.startswith("#"):
            continue
        if value.endswith("\\"):
            pending += value[:-1] + " "
        else:
            entries.append(pending + value)
            pending = ""
    package = r"[A-Za-z0-9][A-Za-z0-9_.-]*(?:\[[A-Za-z0-9_,.-]+\])?==[A-Za-z0-9.!+_-]+"
    hashes = r"(?:\s+--hash=sha256:[0-9a-f]{64})+"
    return bool(entries) and not pending and all(re.fullmatch(package + hashes, item) for item in entries)


def _check_commands(path: Path, violations: list[Violation]) -> None:
    source = path.read_text(encoding="utf-8")
    if re.search(r"(sk-|AKIA[0-9A-Z]{8}|ghp_)", source):
        violations.append(Violation("secrets", f"{path.name}: a string looks like a credential"))
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        violations.append(Violation("commands-syntax", f"{path.name}: {exc}"))
        return
    imported = False
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "agent_sandbox.server":
            if any(alias.name == "command" for alias in node.names):
                imported = True
    if not imported:
        violations.append(
            Violation("commands-import", f"{path.name}: import command from agent_sandbox.server")
        )

    visitor = _CommandVisitor()
    visitor.visit(tree)
    if visitor.visible < 1:
        violations.append(Violation("commands-register", f"{path.name}: register at least one @command"))
    if not visitor.saw_main_start:
        violations.append(
            Violation("commands-start", f"{path.name}: call start() only under if __name__ == '__main__'")
        )
    if visitor.start_outside:
        lines = ", ".join(str(n) for n in visitor.start_outside)
        violations.append(
            Violation("commands-start", f"{path.name}: start() at import time (line {lines})")
        )


class _CommandVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.visible = 0
        self.saw_main_start = False
        self.start_outside: list[int] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if _decorated_command(node) and not _hidden(node):
            self.visible += 1
        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        if _is_main_test(node.test):
            for child in node.body:
                for sub in ast.walk(child):
                    if isinstance(sub, ast.Call) and _is_name(sub.func, "start"):
                        self.saw_main_start = True
            for child in node.orelse:
                self.visit(child)
            return
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if _is_name(node.func, "start"):
            self.start_outside.append(node.lineno)
        self.generic_visit(node)


def _decorated_command(node: ast.FunctionDef) -> bool:
    for deco in node.decorator_list:
        target = deco.func if isinstance(deco, ast.Call) else deco
        if _is_name(target, "command"):
            return True
    return False


def _hidden(node: ast.FunctionDef) -> bool:
    for deco in node.decorator_list:
        if not isinstance(deco, ast.Call):
            continue
        if not _is_name(deco.func, "command"):
            continue
        for keyword in deco.keywords:
            if keyword.arg == "hidden" and isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
                return True
    return False


def _is_name(node: ast.AST, name: str) -> bool:
    return isinstance(node, ast.Name) and node.id == name


def _is_main_test(test: ast.AST) -> bool:
    if not isinstance(test, ast.Compare) or len(test.ops) != 1 or not isinstance(test.ops[0], ast.Eq):
        return False
    values = [test.left, *test.comparators]

    def as_text(node: ast.AST) -> str | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.Name) and node.id == "__name__":
            return "__name__"
        return None

    texts = [as_text(node) for node in values]
    return "__name__" in texts and "__main__" in texts


def _require_str(data: dict, key: str, violations: list[Violation]) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        violations.append(Violation("yaml-field", f"template.yaml: {key} must be a non-empty string"))
        return ""
    return value.strip()


def _check_env(env: object, where: str, violations: list[Violation]) -> None:
    if env is None:
        violations.append(Violation("yaml-field", f"{where}: env must be a mapping"))
        return
    if not isinstance(env, dict):
        violations.append(Violation("yaml-field", f"{where}: env must be a mapping"))
        return
    for key, value in env.items():
        if not isinstance(key, str):
            violations.append(Violation("yaml-env", f"{where}: env key {key!r} must be a string"))
            continue
        if SECRET_KEY.search(key) and value not in ("", None):
            violations.append(
                Violation("secrets", f"{where}: {key} must be an empty string (the value is injected at create)")
            )


def check_directory(template_dir: Path) -> list[Violation]:
    """Return every spec violation for one template directory."""
    violations: list[Violation] = []
    template_dir = template_dir.resolve()
    for name in REQUIRED_FILES:
        if not (template_dir / name).is_file():
            violations.append(Violation("required-file", f"missing {name}"))
    yaml_path = template_dir / "template.yaml"
    data: dict = {}
    if yaml_path.is_file():
        loaded, errors = _load_yaml(yaml_path)
        violations.extend(errors)
        if isinstance(loaded, dict):
            data = loaded

    directory_name = template_dir.name
    name = _require_str(data, "name", violations) if data else ""
    if name and name != directory_name:
        violations.append(
            Violation("yaml-name", f"template.yaml name {name!r} must match the directory {directory_name!r}")
        )
    if name and name != SKELETON_NAME and not NAME_RE.fullmatch(name):
        violations.append(Violation("yaml-name", f"name {name!r} must match {NAME_RE.pattern}"))

    for key in ("description", "version", "author", "license"):
        if data:
            _require_str(data, key, violations)

    base = data.get("base") if data else None
    base_ok = isinstance(base, str) and (base == FC_PLACEHOLDER or FC_PINNED.fullmatch(base) is not None)
    readme_en = template_dir / "README.md"
    en_sections = _check_readme(readme_en, README_EN, violations) if readme_en.is_file() else {}
    zh_sections = {}
    readme_zh = template_dir / "README.zh-CN.md"
    if readme_zh.is_file():
        zh_sections = _check_readme(readme_zh, README_ZH, violations)

    if data.get("spec_version") in (2, 3):
        for label, sections, heading in (
            ("README.md", en_sections, "Quick start (HTTP POST)"),
            ("README.zh-CN.md", zh_sections, "快速开始（HTTP POST）"),
        ):
            body = sections.get(heading, "")
            if body and not all(token in body for token in ("POST", "/commands/", "application/json", '"result"')):
                violations.append(
                    Violation(
                        "readme-http",
                        f"{label}: {heading} must show POST /commands/<name>, application/json, and a result envelope",
                    )
                )
        for label, sections, heading in (
            ("README.md", en_sections, "Quick start (Python SDK)"),
            ("README.zh-CN.md", zh_sections, "快速开始（Python SDK）"),
        ):
            if heading in sections and "agent-sandbox-client" not in sections[heading]:
                violations.append(
                    Violation(
                        "readme-client",
                        f"{label}: {heading} must document the client install as agent-sandbox-client "
                        "(pip install agent-sandbox is an unrelated project)",
                    )
                )
        for label, path in (("README.md", readme_en), ("README.zh-CN.md", readme_zh)):
            if path.is_file() and _bad_client_install(path.read_text(encoding="utf-8")):
                violations.append(
                    Violation(
                        "readme-client",
                        f"{label}: pip install agent-sandbox names an unrelated project; use agent-sandbox-client",
                    )
                )

    if data and not base_ok:
        explained = "Base image" in en_sections and len(en_sections.get("Base image", "")) >= 40
        if explained and isinstance(base, str) and base.strip():
            pass
        else:
            got = base if isinstance(base, str) else type(base).__name__
            violations.append(
                Violation(
                    "base-image",
                    "template.yaml base must be the Alibaba FC image string "
                    f"{FC_PLACEHOLDER!r} or a pinned fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:vX.Y.Z "
                    f"(got {got!r}). A different base needs a README '## Base image' explanation.",
                )
            )

    if data:
        if "spec_version" in data and data["spec_version"] not in (2, 3):
            violations.append(Violation("yaml-field", "spec_version must be 2 or 3 when set"))
        if data.get("spec_version") == 3:
            from template_application import validate_v3

            violations.extend(Violation("yaml-schema", message) for message in validate_v3(data, template_dir))
        elif "application" in data:
            violations.append(Violation("yaml-schema", "application requires spec_version: 3"))
        if data.get("generation") != 2:
            violations.append(Violation("yaml-generation", "generation must be the integer 2"))
        start = data.get("start_cmd")
        ready = data.get("ready_cmd")
        if not isinstance(start, str) or "agent-sandbox-server serve" not in start or "commands.py" not in start:
            violations.append(
                Violation(
                    "yaml-start",
                    "start_cmd must run agent-sandbox-server serve and point at commands.py",
                )
            )
        if not isinstance(ready, str) or "agent-sandbox-server healthcheck" not in ready:
            violations.append(Violation("yaml-ready", "ready_cmd must run agent-sandbox-server healthcheck"))
        resources = data.get("resources")
        if not isinstance(resources, dict):
            violations.append(Violation("yaml-resources", "resources.cpu and resources.memory are required"))
        else:
            cpu = resources.get("cpu")
            memory = resources.get("memory")
            if not isinstance(cpu, int) or isinstance(cpu, bool) or cpu < 1:
                violations.append(Violation("yaml-resources", "resources.cpu must be a positive integer (vCPU)"))
            if not isinstance(memory, int) or isinstance(memory, bool) or memory < 128:
                violations.append(Violation("yaml-resources", "resources.memory must be a positive integer (MB)"))
            valid_cpu = isinstance(cpu, int) and not isinstance(cpu, bool) and cpu >= 1
            valid_memory = isinstance(memory, int) and not isinstance(memory, bool) and memory >= 128
            if valid_cpu and valid_memory and (memory % 64 or not 1024 * cpu <= memory <= 4096 * cpu):
                violations.append(Violation("yaml-resources", "Alibaba FC memory must be a multiple of64MB and1..4GiB per vCPU"))
        ports = data.get("ports")
        if not isinstance(ports, list) or 9000 not in ports:
            violations.append(Violation("yaml-ports", "ports must include 9000"))
        tags = data.get("tags")
        if not isinstance(tags, list) or not tags or not all(isinstance(tag, str) and tag for tag in tags):
            violations.append(Violation("yaml-tags", "tags must be a non-empty list of strings"))
        if data.get("priority") not in {"P0", "P1", "P2"}:
            violations.append(Violation("yaml-wave", "priority must be P0, P1, or P2"))
        if data.get("wave") not in {1, 2, 3, "other"}:
            violations.append(Violation("yaml-wave", "wave must be 1, 2, 3, or other"))
        if "tested_on" not in data or not isinstance(data.get("tested_on"), list):
            violations.append(Violation("yaml-tested", "tested_on must be a list (empty when nothing has passed)"))
        if "env" not in data:
            violations.append(Violation("yaml-field", "template.yaml: env must be a mapping"))
        else:
            _check_env(data.get("env"), "template.yaml", violations)
        smoke = data.get("smoke")
        if not isinstance(smoke, list) or not smoke:
            violations.append(Violation("yaml-smoke", "smoke must list at least one {command, args, expect}"))
        else:
            for index, item in enumerate(smoke):
                if not isinstance(item, dict) or not isinstance(item.get("command"), str) or not item["command"]:
                    violations.append(Violation("yaml-smoke", f"smoke[{index}].command must be a string"))
                elif item.get("args") is not None and not isinstance(item.get("args"), dict):
                    violations.append(Violation("yaml-smoke", f"smoke[{index}].args must be a mapping"))

    dockerfile = template_dir / "Dockerfile"
    if dockerfile.is_file():
        lines = _dockerfile_lines(dockerfile.read_text(encoding="utf-8"))
        froms = [line for line in lines if _instruction(line) == "FROM"]
        if not froms:
            violations.append(Violation("dockerfile-from", "Dockerfile needs a FROM"))
        elif isinstance(base, str) and base_ok and _from_image(froms[0]) != base:
            violations.append(
                Violation("dockerfile-from", f"Dockerfile FROM {_from_image(froms[0])!r} must match base {base!r}")
            )
        for line in lines:
            op = _instruction(line)
            if op in {"CMD", "ENTRYPOINT"}:
                violations.append(
                    Violation(
                        "dockerfile-cmd",
                        "Dockerfile must not set CMD or ENTRYPOINT; the platform start_cmd starts the server",
                    )
                )
        users = [line.split(None, 1)[1] for line in lines if _instruction(line) == "USER"]
        if not users or users[-1] != "user":
            violations.append(Violation("dockerfile-user", "the last USER instruction must be user"))
        workdirs = [line.split(None, 1)[1] for line in lines if _instruction(line) == "WORKDIR"]
        if not workdirs or workdirs[-1] != "/home/user/app":
            violations.append(Violation("dockerfile-workdir", "the last WORKDIR must be /home/user/app"))
        run_lines = [line for line in lines if _instruction(line) == "RUN"]
        if not any(_server_sdk_pinned(line) for line in run_lines):
            violations.append(
                Violation(
                    "pinned-version",
                    "Dockerfile RUN must pin agent-sandbox-server==X.Y.Z or "
                    "agent-sandbox-server @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/"
                    "<40-hex>.tar.gz#subdirectory=server-sdk",
                )
            )
        for line in run_lines:
            if "pip install" not in line:
                continue
            if ".whl" in line:
                continue
            if re.search(r"pip install\b[^&|;]*==", line):
                continue
            if _server_sdk_pinned(line) or _pip_hash_lock(line, template_dir, lines):
                continue
            violations.append(Violation("pinned-version", f"unpinned pip install in Dockerfile: {line}"))
        for line in lines:
            if _instruction(line) == "RUN" and "npm install" in line and "@" not in line.split("npm install", 1)[1]:
                violations.append(Violation("pinned-version", f"unpinned npm install in Dockerfile: {line}"))

    opt_in = template_dir / "server-sdk.commit"
    if opt_in.exists() or opt_in.is_symlink():
        try:
            try:
                from .server_sdk_pin import server_commit
            except ImportError:
                from server_sdk_pin import server_commit
            server_commit(template_dir)
        except (ValueError, OSError) as exc:
            violations.append(Violation("server-sdk-pin", str(exc)))

    commands = template_dir / "commands.py"
    if commands.is_file():
        _check_commands(commands, violations)
    e2e = template_dir / "e2e_test.py"
    if e2e.is_file() and "E2E_BASE_URL" not in e2e.read_text(encoding="utf-8"):
        violations.append(Violation("e2e-local", "e2e_test.py must read E2E_BASE_URL for the local smoke"))

    verified_en = _providers_in(en_sections.get("Verified", ""))
    verified_zh = _providers_in(zh_sections.get("已验证", ""))
    if readme_en.is_file() and readme_zh.is_file() and verified_en != verified_zh:
        violations.append(
            Violation(
                "verified-mismatch",
                f"README verified providers {sorted(verified_en)} differ from README.zh-CN.md {sorted(verified_zh)}",
            )
        )
    tested = data.get("tested_on") if isinstance(data.get("tested_on"), list) else None
    tested_set = {item for item in tested if isinstance(item, str)} if tested is not None else set()
    if tested is not None and tested_set != verified_en:
        violations.append(
            Violation(
                "verified-mismatch",
                f"tested_on {sorted(tested_set)} must match the README Verified providers {sorted(verified_en)}",
            )
        )
    for provider in sorted(verified_en | tested_set):
        if provider not in PROVIDERS:
            violations.append(Violation("verified-provider", f"unknown provider {provider!r}"))
            continue
        if not _evidence_passes(template_dir, provider):
            slugs = " or ".join(f"evidence/{slug}-YYYY-MM-DD.json" for slug in PROVIDERS[provider])
            violations.append(
                Violation(
                    "verified-evidence",
                    f"{provider} is listed as verified but no passing evidence for this template/version ({slugs}) "
                    "records cli and sdk results",
                )
            )

    if name and name != SKELETON_NAME and data.get("spec_version") in (2, 3):
        design = template_dir.parent / "docs" / "design" / f"{name}.md"
        if template_dir.parent.name == "docs":
            design = template_dir.parent / "design" / f"{name}.md"
        # Templates live next to docs/ at the repo root. A copied fixture has no docs/.
        docs_root = template_dir.parent / "docs" / "design"
        if docs_root.is_dir() or (template_dir.parent / "awesome-templates.yaml").is_file():
            if not design.is_file():
                violations.append(Violation("design-doc", f"missing docs/design/{name}.md"))
            else:
                design_sections = _sections(design.read_text(encoding="utf-8"))
                for heading in DESIGN_HEADINGS:
                    if heading not in design_sections or len(design_sections[heading].strip()) < 3:
                        violations.append(Violation("design-doc", f"docs/design/{name}.md missing '## {heading}'"))
                feasibility = design_sections.get("Express feasibility", "")
                if "Limiting factor:" not in feasibility:
                    violations.append(
                        Violation("design-doc", f"docs/design/{name}.md Express feasibility needs 'Limiting factor:'")
                    )

    if (template_dir.parent / "awesome-templates.yaml").is_file() and name and name != SKELETON_NAME:
        if data.get("spec_version") in (2, 3):
            entries = _index_entries(template_dir.parent) or []
            match = [item for item in entries if item.get("path") == name or item.get("name") == name]
            if not match:
                violations.append(Violation("index", f"awesome-templates.yaml has no entry for {name}"))
            else:
                item = match[0]
                if item.get("name") != name or item.get("path") != name:
                    violations.append(Violation("index", f"index name/path must both be {name}"))
                if item.get("status") not in {"official", "community", "experimental"}:
                    violations.append(Violation("index", f"index status for {name} is not a known value"))
                declared = data.get("capabilities")
                indexed = item.get("capabilities")
                if not all(isinstance(value, list) and all(isinstance(cap, str) for cap in value)
                           for value in (declared, indexed)):
                    violations.append(Violation("index-capabilities", f"{name}: template and index capabilities must be string lists"))
                elif set(declared) != set(indexed):
                    violations.append(Violation("index-capabilities", f"{name}: template and index capabilities must match"))
    return violations


def claims_spec(template_dir: Path) -> bool:
    path = template_dir / "template.yaml"
    if not path.is_file():
        return False
    loaded, errors = _load_yaml(path)
    if errors or not isinstance(loaded, dict):
        return True  # malformed manifests cannot opt out by breaking the version parse
    return "spec_version" in loaded


def iter_templates(root: Path) -> list[Path]:
    found: list[Path] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir() or child.name.startswith("."):
            continue
        if (child / "template.yaml").is_file():
            found.append(child)
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lint a template directory against the template spec.")
    parser.add_argument("template", nargs="?", help="Template directory. Omit with --all.")
    parser.add_argument("--all", action="store_true", help="Lint every template under the repo root.")
    parser.add_argument("--strict", action="store_true", help="Fail --all on legacy violations too.")
    parser.add_argument("--root", type=Path, default=ROOT, help="Repository root for --all.")
    parser.add_argument("--verbose", action="store_true", help="Print every violation in --all mode.")
    args = parser.parse_args(argv)

    if args.all:
        templates = iter_templates(args.root)
        if not templates:
            print("no template directories found", file=sys.stderr)
            return 1
        claimed_failed = False
        any_failed = False
        print("CONFORMANCE")
        conformant: list[str] = []
        rows: list[str] = []
        for directory in templates:
            violations = check_directory(directory)
            claimed = claims_spec(directory)
            if not violations and claimed:
                conformant.append(directory.name)
                continue
            if not violations:
                conformant.append(directory.name)
                continue
            any_failed = True
            if claimed:
                claimed_failed = True
            codes = sorted({item.code for item in violations})
            kind = "spec" if claimed else "legacy"
            rows.append(
                f"  {directory.name}  {kind}  {len(violations)}  {', '.join(codes)}"
            )
            if args.verbose or claimed:
                for item in violations:
                    print(f"    {directory.name}: {item}")
        print("conformant:")
        for name in conformant:
            print(f"  {name}")
        print("non-conformant:")
        if rows:
            print("\n".join(rows))
        else:
            print("  (none)")
        print(f"claimed spec failures: {sum(1 for line in rows if '  spec  ' in line)}")
        if args.strict:
            return 1 if any_failed else 0
        return 1 if claimed_failed else 0

    if not args.template:
        parser.error("pass a template directory or --all")
    directory = Path(args.template)
    if not directory.is_dir():
        print(f"not a directory: {directory}", file=sys.stderr)
        return 1
    violations = check_directory(directory)
    if not violations:
        print(f"conformant: {directory.name}")
        return 0
    for item in violations:
        print(f"{directory}: {item}")
    print(f"{len(violations)} violation(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
