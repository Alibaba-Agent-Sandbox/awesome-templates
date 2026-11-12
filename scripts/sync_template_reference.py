#!/usr/bin/env python3
"""Generate readable bilingual field tables from the canonical schema, without evaluation."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

# Field meanings are editorial text. Types, required fields, limits and defaults come
# from the actual schema/normalizer contract, so this does not define another format.
PURPOSES = {
    "specVersion": ("Public resource format version.", "公开资源格式版本。"),
    "name": ("Resource name.", "资源名称。"),
    "sandbox": ("Sandbox template and instance settings.", "Sandbox 模板与实例设置。"),
    "deployment": ("Native Serverless Devs project.", "原生 Serverless Devs 项目。"),
    "application": ("Select the Agents API coordinator.", "选择 Agents API 协调器。"),
    "provider": ("Provider selected before execution.", "执行前选定的 Provider。"),
    "template": (
        "Environment source, image or existing reference.",
        "运行环境的源码、镜像或已有引用。",
    ),
    "source": ("Contained source build recipe.", "模板目录内的源码构建配方。"),
    "image": ("Container image input.", "容器镜像输入。"),
    "reference": (
        "Existing Provider-native template ID; never translated across Providers.",
        "已有 Provider 原生模板 ID，不跨 Provider 转换。",
    ),
    "aliases": ("Template lookup names.", "模板查找别名。"),
    "props": ("Stage-specific properties.", "对应阶段的配置参数。"),
    "instance": (
        "Instance creation settings, separate from preparation.",
        "实例创建设置，与模板准备分开。",
    ),
    "start": ("One workload startup command.", "工作负载的一次启动命令。"),
    "ready": ("Workload readiness command.", "工作负载就绪检查命令。"),
    "services": ("Named business service contracts.", "有名称的业务服务契约。"),
    "ports": (
        "Additional access ports; no listener or protocol promise.",
        "额外访问端口，不承诺监听已启动或存在特定协议。",
    ),
    "timeout": (
        "Instance lifetime in seconds; maximum 86400.",
        "实例最长寿命，单位秒，最大86400。",
    ),
    "envs": ("Declared guest environment values.", "声明的 Guest 环境变量值。"),
    "metadata": ("Provider instance metadata.", "Provider 实例元数据。"),
    "cpu": ("vCPU count for this stage.", "当前阶段的 vCPU 数。"),
    "memory": (
        "Memory amount; Express uses MB, other adapters retain their input units.",
        "内存数量；Express 使用 MB，其他适配器按对应输入单位。",
    ),
    "disk": ("Instance disk amount in MB.", "实例磁盘数量，单位 MB。"),
    "gpu": (
        "Provider GPU selector; OpenSandbox requires a count string.",
        "Provider GPU 规格；OpenSandbox 要求数量字符串。",
    ),
    "secure": ("OpenSandbox secure-mode setting.", "OpenSandbox 安全模式设置。"),
    "volume_mounts": (
        "Guest mount path to existing volume name; no volume creation.",
        "Guest 挂载路径到已有卷名称的映射，不创建卷。",
    ),
    "lifecycle": ("Instance timeout policy.", "实例超时后的处理策略。"),
    "onTimeout": ("Pause or delete the instance on timeout.", "超时后暂停或删除实例。"),
    "autoResume": (
        "Automatic resume; requires onTimeout=pause.",
        "自动恢复，仅适用于 onTimeout=pause。",
    ),
    "provider_options": (
        "Selected Provider's integrated create options.",
        "所选 Provider 已接入的创建选项。",
    ),
    "entrypoint": (
        "OpenSandbox container entrypoint command.",
        "OpenSandbox 容器启动命令。",
    ),
    "ready_timeout": (
        "OpenSandbox readiness wait in seconds.",
        "OpenSandbox 就绪等待秒数。",
    ),
    "network_policy": (
        "OpenSandbox network-policy selector.",
        "OpenSandbox 网络策略选择值。",
    ),
    "platform": (
        "Container operating system and architecture.",
        "容器操作系统与架构。",
    ),
    "secure_access": (
        "OpenSandbox secure-access option.",
        "OpenSandbox 安全访问选项。",
    ),
    "edition": ("Native Devs project edition.", "原生 Devs 项目规范版本。"),
    "access": (
        "Existing Serverless Devs credential alias.",
        "已有 Serverless Devs 凭据别名。",
    ),
    "vars": ("Native project variables.", "原生项目变量。"),
    "resources": (
        "Native component resources keyed by project ID.",
        "按项目资源 ID 声明的原生组件资源。",
    ),
    "component": (
        "Actual native component identifier and version.",
        "实际原生组件标识与版本。",
    ),
    "actions": ("Native Devs lifecycle actions.", "原生 Devs 生命周期 actions。"),
    "flow": ("Native Devs execution flow.", "原生 Devs 执行顺序。"),
    "validation": ("Native project validation setting.", "原生项目校验设置。"),
    "type": ("Declared application or hook type.", "应用或 hook 的声明类型。"),
    "roles": (
        "References to three distinct native FC resources.",
        "引用三个不同的原生 FC 资源。",
    ),
    "gateway": ("Public Gateway resource ID.", "公开 Gateway 的资源 ID。"),
    "worker": ("Private Worker resource ID.", "私有 Worker 的资源 ID。"),
    "dispatcher": ("Private Dispatcher resource ID.", "私有 Dispatcher 的资源 ID。"),
    "server": (
        "Server image source or digest-pinned image.",
        "Server 镜像源码或固定 digest 的镜像。",
    ),
    "sessions": (
        "Managed Session admission and retention settings.",
        "托管 Session 准入和结果保留设置。",
    ),
    "idleTimeoutSeconds": (
        "Session idle timeout in seconds.",
        "Session 空闲超时秒数。",
    ),
    "maxLogicalSessionsPerOwner": (
        "Maximum logical Sessions per owner.",
        "每个 owner 的逻辑 Session 上限。",
    ),
    "maxActiveSessions": ("Active Session admission limit.", "活跃 Session 准入上限。"),
    "maxQueuedTurnsPerSession": (
        "Queued turns per Session.",
        "每个 Session 的排队轮次上限。",
    ),
    "resultRetentionSeconds": (
        "Committed-result retention in seconds.",
        "已提交结果的保留秒数。",
    ),
    "storage": ("File and artifact storage bounds.", "文件和产物存储上限。"),
    "maxFileBytes": (
        "Maximum input file size in bytes.",
        "输入文件大小上限，单位字节。",
    ),
    "maxArtifactBytes": (
        "Maximum individual artifact size in bytes.",
        "单个产物大小上限，单位字节。",
    ),
    "maxTurnArtifactBytes": (
        "Total artifact bytes per turn.",
        "每轮产物总字节数上限。",
    ),
    "maxRetainedBytesPerOwner": (
        "Retained bytes per owner.",
        "每个 owner 的保留总字节数上限。",
    ),
    "limits": ("Run, queue, event and output budgets.", "运行、排队、事件和输出预算。"),
    "maxRunSeconds": ("Run time budget in seconds.", "运行时间预算，单位秒。"),
    "maxToolSeconds": (
        "Tool-call time budget in seconds.",
        "工具调用时间预算，单位秒。",
    ),
    "maxConcurrentRuns": ("Concurrent-run admission budget.", "并发运行准入预算。"),
    "maxQueuedRuns": ("Queued-run admission budget.", "排队运行准入预算。"),
    "maxRunsPerMinute": ("Run admission budget per minute.", "每分钟运行准入预算。"),
    "maxEventsPerRun": ("Event count bound per run.", "每次运行的事件数量上限。"),
    "maxOutputBytes": ("Captured output bound in bytes.", "采集输出的字节数上限。"),
    "maxSubscribersPerSession": (
        "Concurrent event subscribers per Session.",
        "每个 Session 的并发事件订阅数上限。",
    ),
    "state": (
        "Existing durable database and optional connection settings.",
        "已有持久数据库及可选连接设置。",
    ),
    "databaseUrl": (
        "Existing PostgreSQL connection URL; Server-only.",
        "已有 PostgreSQL 连接 URL，仅供 Server 使用。",
    ),
    "databaseCa": (
        "Optional private database CA certificate PEM.",
        "可选的数据库私有 CA 证书 PEM。",
    ),
    "vpcConfig": (
        "Existing FC network configuration; see the Managed reference.",
        "已有 FC 网络配置，结构见托管应用参考。",
    ),
    "bindings": ("Local business and credential inputs.", "本地业务及凭据配置。"),
    "sandboxAccess": (
        "Server-only Sandbox lifecycle access.",
        "仅供 Server 管理 Sandbox 生命周期的配置。",
    ),
    "apiKey": ("Referenced service API key.", "通过引用提供的服务 API Key。"),
    "baseUrl": ("Explicit service API base URL.", "明确的服务 API 基础 URL。"),
    "domain": (
        "Sandbox endpoint domain from the selected platform.",
        "所选平台提供的 Sandbox 访问域名。",
    ),
    "region": ("Matching target region.", "与目标资源一致的地域。"),
    "model": (
        "Allowed model identifier or model-access configuration.",
        "允许使用的模型标识或模型访问配置。",
    ),
    "adapter": (
        "Agent CLI adapter matching the model API.",
        "与模型 API 对应的 Agent CLI 适配器。",
    ),
    "clientAuth": (
        "Generated business credentials or explicit token hashes.",
        "自动生成的业务凭据或显式令牌哈希。",
    ),
    "internalAuth": (
        "Separate private control-plane authentication.",
        "独立的内部控制认证。",
    ),
    "generate": (
        "Generate and safely reuse a local credential.",
        "自动生成并安全复用本机凭据。",
    ),
    "owner": ("Business credential owner.", "业务凭据所属 owner。"),
    "tokens": (
        "Explicit accepted business-token hashes.",
        "显式允许的业务令牌哈希列表。",
    ),
    "sha256": (
        "Lowercase SHA256 of a business token, never its plaintext.",
        "业务令牌的小写 SHA256，不是令牌明文。",
    ),
    "scopes": ("Allowed business API scopes.", "允许的业务 API 权限范围。"),
    "expiresAt": ("Credential expiration timestamp.", "凭据过期时间戳。"),
    "token": ("Referenced private internal token.", "通过引用提供的内部令牌。"),
    "roleArn": (
        "Existing FC execution role; must agree with native roles.",
        "已有 FC 执行角色，须与原生 role 声明一致。",
    ),
    "ingress": (
        "Stable Gateway alias or domain route.",
        "稳定的 Gateway 别名或域名路由。",
    ),
    "kind": ("Gateway ingress mode.", "Gateway 入口模式。"),
    "aliasName": ("Stable FC alias name.", "稳定的 FC 别名。"),
    "allowTestDomain": (
        "Explicitly allow the FC test domain.",
        "显式允许使用 FC 测试域名。",
    ),
    "domainName": ("Configured HTTPS custom domain.", "配置的 HTTPS 自定义域名。"),
    "protocol": (
        "Declared service protocol, or HTTPS for custom-domain ingress.",
        "服务协议；自定义域名入口使用 HTTPS。",
    ),
    "path": ("Custom-domain root route.", "自定义域名的根路由。"),
    "hooks": ("Optional bounded deployment checks.", "可选的有界部署检查。"),
    "beforeApply": (
        "Checks before applying deployment changes.",
        "应用部署变更前的检查。",
    ),
    "afterReady": (
        "Checks after the candidate becomes ready.",
        "候选部署就绪后的检查。",
    ),
    "id": ("Unique hook identifier across phases.", "跨阶段唯一的 hook 标识。"),
    "argv": (
        "Executable and arguments; no implicit shell.",
        "可执行文件与参数，不隐式启动 shell。",
    ),
    "cwd": (
        "Contained working directory relative to the template.",
        "相对模板目录且不越界的工作目录。",
    ),
    "timeoutSeconds": ("Hook time budget in seconds.", "hook 时间预算，单位秒。"),
    "envAllowlist": (
        "Host variable names allowed into this hook.",
        "允许传入此 hook 的主机变量名。",
    ),
    "step": (
        "Managed role inspected by the native info command.",
        "由原生 info 命令检查的托管角色。",
    ),
    "command": ("Read-only native component command.", "只读的原生组件命令。"),
    "dockerfile": (
        "Dockerfile inside the template directory.",
        "模板目录内的 Dockerfile。",
    ),
    "context": (
        "Build context rooted in the template directory.",
        "以模板目录为根的构建上下文。",
    ),
    "profiles": ("Explicit alternate source recipes.", "显式选择的替代源码配方。"),
    "port": ("Service access port.", "服务访问端口。"),
    "version": ("Service protocol contract version.", "服务协议的契约版本。"),
    "operations": (
        "Described service operations; not a permission grant.",
        "描述的服务操作，不授予权限。",
    ),
}
TYPE_LABELS = {
    "expression": ("native expression", "原生表达式"),
    "positiveIntegerInput": ("positive integer or expression", "正整数或表达式"),
    "nonnegativeIntegerInput": (
        "nonnegative integer or expression",
        "非负整数或表达式",
    ),
    "booleanInput": ("boolean or expression", "布尔值或表达式"),
    "secret": ("secret expression", "秘密值表达式"),
    "componentProps": ("native object or expression", "原生对象或表达式"),
}


def escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def literal(value: Any) -> str:
    if isinstance(value, dict):
        return "empty map" if not value else "see child defaults"
    if isinstance(value, list):
        return "empty list" if not value else ", ".join(literal(item) for item in value)
    return "`" + escape(json.dumps(value, ensure_ascii=False)) + "`"


def anchor(pointer: str) -> str:
    if not pointer:
        return "template"
    if pointer.startswith("/$defs/"):
        value = "type-" + pointer[7:]
    else:
        value = "field-" + pointer.removeprefix("/").replace("properties/", "")
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


@dataclass
class Section:
    pointer: str
    title: str
    schema: dict[str, Any]
    inherited: dict[str, Any] | None = None


class Reference:
    def __init__(self, schema: dict[str, Any], contract: dict[str, Any], language: str):
        self.schema, self.contract = schema, contract
        self.zh = language == "zh-CN"
        self.sections: dict[str, Section] = {}
        self.covered_fields: set[str] = set()
        self.add("", "template", schema)
        for key, value in schema["$defs"].items():
            self.add("/$defs/" + key, key, value)

    def text(self, en: str, zh: str) -> str:
        return zh if self.zh else en

    def object_like(self, data: dict[str, Any]) -> bool:
        return data.get("type") == "object" or "properties" in data

    def complex(self, data: dict[str, Any]) -> bool:
        return self.object_like(data) or any(
            self.object_like(item) for item in data.get("oneOf", [])
        )

    def choice_label(self, data: dict[str, Any], index: int) -> str:
        fields = data.get("properties", {})
        for key in ("type", "generate"):
            if "const" in fields.get(key, {}):
                return key + "=" + str(fields[key]["const"]).lower()
        if "tokens" in fields:
            return self.text("explicit tokens", "显式令牌")
        if "token" in fields:
            return self.text("explicit token", "显式令牌")
        return self.text("choice ", "分支 ") + str(index + 1)

    def condition(self, data: dict[str, Any]) -> str:
        return ", ".join(
            key + "=" + str(value["const"])
            for key, value in data.get("properties", {}).items()
            if "const" in value
        )

    def add(self, pointer: str, title: str, data: dict[str, Any], inherited=None):
        if pointer in self.sections:
            return
        self.sections[pointer] = Section(pointer, title, data, inherited)
        for key, child in data.get("properties", {}).items():
            child_pointer = pointer + "/properties/" + key
            self.covered_fields.add(child_pointer)
            child_title = key if not pointer else title + "." + key
            parent_child = (inherited or {}).get("properties", {}).get(key)
            self.discover(child_pointer, child_title, child, parent_child)
        for key, label in (("items", "[]"), ("additionalProperties", ".<name>")):
            child = data.get(key)
            if isinstance(child, dict):
                self.discover(pointer + "/" + key, title + label, child)
        for index, child in enumerate(data.get("oneOf", [])):
            if self.object_like(child):
                self.add(
                    pointer + "/oneOf/" + str(index),
                    title + " — " + self.choice_label(child, index),
                    child,
                )
        for index, branch in enumerate(data.get("allOf", [])):
            if "then" in branch:
                self.add(
                    pointer + "/allOf/" + str(index) + "/then",
                    title + " — " + self.condition(branch.get("if", {})),
                    branch["then"],
                    data,
                )

    def discover(self, pointer, title, data, inherited=None):
        if self.complex(data):
            self.add(pointer, title, data, inherited)
        elif data.get("type") == "array" and isinstance(data.get("items"), dict):
            self.discover(pointer + "/items", title + "[]", data["items"])

    def link(self, pointer: str, label: str) -> str:
        return "[" + escape(label) + "](#" + anchor(pointer) + ")"

    def type_text(self, data: dict[str, Any], pointer: str) -> str:
        if "$ref" in data:
            name = data["$ref"].rsplit("/", 1)[-1]
            label = TYPE_LABELS.get(name, (name, name))[self.zh]
            return self.link("/$defs/" + name, label)
        if self.object_like(data):
            label = (
                self.choice_label(data, int(pointer.rsplit("/", 1)[-1]))
                if "/oneOf/" in pointer and pointer.rsplit("/", 1)[-1].isdigit()
                else self.text("fields", "子字段")
            )
            return "object · " + self.link(pointer, label)
        if "oneOf" in data:
            return self.text(" or ", " / ").join(
                dict.fromkeys(
                    self.type_text(child, pointer + "/oneOf/" + str(index))
                    for index, child in enumerate(data["oneOf"])
                )
            )
        if data.get("type") == "array":
            return self.text("array of ", "数组，每项为 ") + self.type_text(
                data.get("items", {}), pointer + "/items"
            )
        if "const" in data:
            value = data["const"]
            return (
                "boolean"
                if isinstance(value, bool)
                else "integer"
                if isinstance(value, int)
                else "string"
            )
        if "enum" in data:
            return "string"
        return str(data.get("type", self.text("native JSON value", "原生 JSON 值")))

    def constraints(self, data: dict[str, Any]) -> str:
        values = []
        if "const" in data:
            values.append("= " + literal(data["const"]))
        if "enum" in data:
            values.append(", ".join(literal(value) for value in data["enum"]))
        for key, prefix in (
            ("minimum", "≥"),
            ("maximum", "≤"),
            ("minItems", "items ≥"),
            ("maxItems", "items ≤"),
            ("minProperties", "fields ≥"),
            ("maxProperties", "fields ≤"),
            ("minLength", "length ≥"),
            ("maxLength", "length ≤"),
        ):
            if key in data:
                values.append(prefix + " " + str(data[key]))
        if data.get("uniqueItems"):
            values.append(self.text("unique items", "元素不重复"))
        if "pattern" in data:
            pattern = data["pattern"]
            if pattern.startswith("^\\$\\{"):
                values.append(
                    self.text(
                        "native `${...}`; evaluated by Devs",
                        "原生 `${...}`，由 Devs 求值",
                    )
                )
            elif "sha256:" in pattern:
                values.append(
                    self.text(
                        "image@sha256:64 lowercase hex digits",
                        "image@sha256:64位小写十六进制",
                    )
                )
            elif "{64}" in pattern:
                values.append(self.text("64 lowercase hex digits", "64位小写十六进制"))
            elif "{0,62}" in pattern:
                values.append(
                    self.text(
                        "ASCII kebab-case, 1–63 characters",
                        "ASCII kebab-case，1–63字符",
                    )
                )
            elif "{0,127}" in pattern:
                values.append(
                    self.text(
                        "ASCII reference ID, 1–128 characters",
                        "ASCII引用标识，1–128字符",
                    )
                )
            elif pattern.startswith("^/"):
                values.append(
                    self.text(
                        "absolute mount path; system paths excluded",
                        "绝对挂载路径，排除系统目录",
                    )
                )
            elif "A-Za-z]:" in pattern:
                values.append(self.text("contained relative path", "不越界的相对路径"))
            else:
                values.append(self.text("complete ASCII identifier", "完整ASCII标识"))
        if data.get("type") == "array":
            item = self.constraints(data.get("items", {}))
            if item != "—":
                values.append(self.text("each: ", "每项：") + item)
        for branch in data.get("oneOf", []):
            if not self.object_like(branch) and "$ref" not in branch:
                branch_constraints = self.constraints(branch)
                if branch_constraints != "—":
                    values.append(
                        self.text("literal: ", "字面值：") + branch_constraints
                    )
        return "; ".join(values) or "—"

    def defaults(self, section: Section, key: str, data: dict[str, Any]) -> str:
        if "default" in data:
            return literal(data["default"])
        pointer = section.pointer
        if section.title == "deployment":
            return {
                "name": self.text("root name", "根 name"),
                "access": literal("default"),
            }.get(key, "—")
        if pointer == "/properties/sandbox" and key == "provider":
            return self.text(
                "CLI/context; agents-api: alicloud-express",
                "CLI/调用上下文；agents-api: alicloud-express",
            )
        if "then/properties/template/properties/props" in pointer:
            value = self.contract["templateDefaults"].get(key)
            if value is not None:
                return literal(value) + (
                    self.text("; agents-api:4096", "；agents-api:4096")
                    if key == "memory"
                    else ""
                )
        if section.title in {"source", "recipe"}:
            return {"dockerfile": literal("Dockerfile"), "context": literal(".")}.get(
                key, "—"
            )
        if section.title == "service" and key == "operations":
            return self.text("empty list", "空列表")
        if section.title == "sandbox.instance" or section.title.startswith("instance_"):
            if key == "timeout":
                return self.text("300; agents-api:3600", "300；agents-api:3600")
            if key in {"envs", "metadata"}:
                return self.text("empty map", "空映射")
        for group in ("sessions", "limits", "storage"):
            if section.title == "application." + group:
                value = self.contract["managedDefaults"][group].get(key)
                if value is not None:
                    return literal(value)
        if (
            section.title.startswith("application.bindings.clientAuth")
            and key == "owner"
        ):
            return (
                literal("default")
                if "generate" in section.schema.get("properties", {})
                else "—"
            )
        if section.title == "application.bindings" and key in {
            "clientAuth",
            "internalAuth",
        }:
            return self.text("generated credentials", "自动生成凭据")
        if section.title == "application.bindings.ingress" and key == "aliasName":
            return literal("prod")
        return "—"

    def purpose(self, section: Section, key: str) -> str:
        if key == "props":
            return (
                self.text(
                    "Selected Provider preparation inputs; see its conditional fields.",
                    "所选 Provider 的准备参数，见对应条件字段。",
                )
                if section.title.startswith("sandbox")
                else self.text(
                    "Native component-owned props; not a duplicated FC schema.",
                    "原生组件定义的 props，不复制 FC schema。",
                )
            )
        if key == "template" and section.title == "deployment":
            return self.text(
                "Native Devs project template settings.",
                "原生 Devs 项目的 template 设置。",
            )
        if key == "name" and section.title == "deployment":
            return self.text("Native project name.", "原生项目名称。")
        if key == "image" and section.title == "application.server":
            return self.text(
                "Digest-pinned Server image, exclusive with source.",
                "固定 digest 的 Server 镜像，与 source 二选一。",
            )
        if key not in PURPOSES:
            raise ValueError(
                "Missing human field meaning: " + section.title + "." + key
            )
        return PURPOSES[key][self.zh]

    def notes(self, section: Section) -> list[str]:
        data = section.schema
        notes = []
        if data.get("additionalProperties") is False:
            notes.append(self.text("Other fields are rejected.", "不接受其他字段。"))
        if "then/properties/template/properties/props" in section.pointer:
            notes.append(
                self.text(
                    "Project preparation checks memory ≥128 and a multiple of64; Express also requires1024–4096 per vCPU. Values are checked after native expression resolution. Backend limits remain Provider-owned.",
                    "项目准备阶段要求 memory ≥128 且为64的倍数；Express 还要求每 vCPU 对应1024–4096。原生表达式求值后检查数值；后端限制仍以 Provider 为准。",
                )
            )
        for combinator, words in (
            ("oneOf", ("Choose exactly one: ", "以下字段仅选一个：")),
            ("anyOf", ("At least one: ", "至少填写一个：")),
        ):
            choices = [item.get("required") for item in data.get(combinator, [])]
            if choices and all(choices):
                notes.append(
                    words[self.zh]
                    + "; ".join(
                        ", ".join("`" + key + "`" for key in choice)
                        for choice in choices
                    )
                    + "."
                )
        for key, required in data.get("dependentRequired", {}).items():
            notes.append(
                "`"
                + key
                + "` "
                + self.text("requires ", "要求同时提供 ")
                + ", ".join("`" + name + "`" for name in required)
                + "."
            )
        required = data.get("required", [])
        if required and not data.get("properties"):
            notes.append(
                self.text("Required inherited fields: ", "必填的上层字段：")
                + ", ".join("`" + name + "`" for name in required)
                + "."
            )
        excluded = data.get("not", {})
        forbidden = excluded.get("required", [])
        forbidden += [
            name
            for branch in excluded.get("anyOf", [])
            for name in branch.get("required", [])
        ]
        if forbidden:
            notes.append(
                self.text("Do not provide: ", "不得填写：")
                + ", ".join("`" + name + "`" for name in forbidden)
                + "."
            )
        for index, branch in enumerate(data.get("allOf", [])):
            if "then" in branch:
                notes.append(
                    self.link(
                        section.pointer + "/allOf/" + str(index) + "/then",
                        self.text("When ", "当 ")
                        + self.condition(branch.get("if", {})),
                    )
                )
        return notes

    def render(self) -> str:
        lines = [
            self.text("# YAML v1 field reference", "# YAML v1 字段全表"),
            "",
            self.text(
                "Fields are grouped by their YAML path. Required means required when that object or branch is used. Defaults come from the shared normalizer; a dash means no default is declared.",
                "字段按 YAML 路径分组。必填表示使用该对象或分支时必须填写；默认值来自共享 normalizer，破折号表示未声明默认值。",
            ),
            "",
            self.text(
                "[Usage and units](template-spec.md) · [Managed semantics](managed-agent-applications.md) · [Machine schema](../spec/template-v1.schema.json)",
                "[用法和单位](template-spec.zh-CN.md) · [托管应用语义](managed-agent-applications.zh-CN.md) · [机器规范](../spec/template-v1.schema.json)",
            ),
            "",
            self.text(
                "This is the integrated high-level input subset. Native Devs/FC object fields belong to the selected component; this table neither duplicates its schema nor claims unintegrated Provider APIs.",
                "这里列出已接入的高层输入子集。原生 Devs/FC 对象的内部字段由所选组件定义；本表不复制其 schema，也不声称已接入其他 Provider API。",
            ),
            "",
        ]
        for section in self.sections.values():
            lines += [
                '<a id="' + anchor(section.pointer) + '"></a>',
                "",
                "## " + section.title,
                "",
            ]
            data = section.schema
            fields = list(data.get("properties", {}).items())
            required = set(data.get("required", [])) | set(
                (section.inherited or {}).get("required", [])
            )
            if fields:
                lines += [
                    self.text(
                        "| Field | Type | Required | Default | Constraints | Purpose |",
                        "| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |",
                    ),
                    "| --- | --- | --- | --- | --- | --- |",
                ]
                for key, value in fields:
                    pointer = section.pointer + "/properties/" + key
                    lines.append(
                        "| `"
                        + key
                        + "` | "
                        + self.type_text(value, pointer)
                        + " | "
                        + self.text(
                            "yes" if key in required else "no",
                            "是" if key in required else "否",
                        )
                        + " | "
                        + self.defaults(section, key, value)
                        + " | "
                        + escape(self.constraints(value))
                        + " | "
                        + escape(self.purpose(section, key))
                        + " |"
                    )
                lines.append("")
            elif "oneOf" in data:
                lines += [self.type_text(data, section.pointer), ""]
                if self.constraints(data) != "—":
                    lines += [self.constraints(data), ""]
            elif isinstance(data.get("additionalProperties"), dict):
                lines += [
                    self.text("Each map value: ", "每个映射值：")
                    + self.type_text(
                        data["additionalProperties"],
                        section.pointer + "/additionalProperties",
                    ),
                    "",
                ]
                if data.get("propertyNames"):
                    lines += [
                        self.text("Map keys: ", "映射键：")
                        + self.constraints(data["propertyNames"]),
                        "",
                    ]
            elif data.get("type") != "object" and not section.inherited:
                lines += [
                    self.type_text(data, section.pointer)
                    + "; "
                    + self.constraints(data),
                    "",
                ]
            elif not section.inherited:
                if section.title == "sandbox.template.props":
                    lines += [
                        self.text(
                            "Preparation fields depend on the selected Provider:",
                            "按所选 Provider 查看准备字段：",
                        ),
                        "",
                    ]
                    for index, branch in enumerate(
                        self.schema["properties"]["sandbox"]["allOf"]
                    ):
                        pointer = (
                            "/properties/sandbox/allOf/"
                            + str(index)
                            + "/then/properties/template/properties/props"
                        )
                        lines += [
                            "- " + self.link(pointer, self.condition(branch["if"]))
                        ]
                    lines.append("")
                elif section.title == "sandbox.instance.provider_options":
                    lines += [
                        self.link(
                            "/$defs/openSandboxOptions",
                            self.text("OpenSandbox options", "OpenSandbox 选项"),
                        ),
                        "",
                    ]
                elif section.title == "application.state.vpcConfig":
                    lines += [
                        self.text(
                            "Existing network IDs: see [configuration and bindings](managed-agent-applications.md#configuration-and-bindings).",
                            "已有网络 ID 结构见[配置与绑定](managed-agent-applications.zh-CN.md#配置与绑定)。",
                        ),
                        "",
                    ]
                else:
                    lines += [
                        self.text(
                            "Object contents are defined by the native component or linked usage reference.",
                            "对象内部字段由原生组件或对应使用参考定义。",
                        ),
                        "",
                    ]
            lines += ["- " + note for note in self.notes(section)] + [""]
        return "\n".join(lines)


def generate(language: str) -> str:
    return Reference(
        json.loads((ROOT / "spec/template-v1.schema.json").read_text()),
        json.loads((ROOT / "contracts/template-v1/contract.json").read_text()),
        language,
    ).render()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for language, suffix in (("en", ""), ("zh-CN", ".zh-CN")):
        path = ROOT / f"docs/template-fields{suffix}.md"
        text = generate(language)
        if args.check:
            if not path.exists() or path.read_text() != text:
                raise SystemExit("stale field reference: " + str(path))
        else:
            path.write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
