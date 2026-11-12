#!/usr/bin/env python3
"""Generate bilingual field tables from the canonical resource schema (no evaluation)."""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def generate(language):
    schema = json.loads((ROOT / "spec/template-v1.schema.json").read_text())
    zh = language == "zh-CN"
    lines = [
        ("# YAML v1 字段全表" if zh else "# YAML v1 field reference"),
        "",
        (
            "本表由规范生成。`$ref` 链接到同页的类型定义；这是已接入的高层参数子集，不是云端所有 API。原生 FC `props` 由选定组件定义。"
            if zh
            else "Generated from the canonical schema. `$ref` links name types below. This is the integrated high-level input subset, not every native cloud API. The selected component defines native FC `props`."
        ),
        "",
        (
            "[使用和单位说明](template-spec.zh-CN.md) · [源 Schema](../spec/template-v1.schema.json)"
            if zh
            else "[Usage and units](template-spec.md) · [Source schema](../spec/template-v1.schema.json)"
        ),
        "",
    ]

    def section(name, data):
        lines.extend(
            [
                "## " + name,
                "",
                "| "
                + (
                    "字段 | 类型 / 取值 / 约束 | 必填 |"
                    if zh
                    else "Field | Type / values / constraints | Required |"
                ),
                "| --- | --- | --- |",
            ]
        )
        for key, value in data.get("properties", {}).items():
            constraints = json.dumps(
                value, ensure_ascii=False, separators=(",", ":")
            ).replace("|", "\\|")
            lines.append(
                "| `"
                + key
                + "` | `"
                + constraints
                + "` | "
                + ("yes" if key in data.get("required", []) else "no")
                + " |"
            )
        if not data.get("properties"):
            lines.append(
                "| — | `"
                + json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace(
                    "|", "\\|"
                )
                + "` | — |"
            )
        if data.get("additionalProperties") is False:
            lines.extend(
                ["", "其他字段不接受。" if zh else "Other fields are rejected."]
            )
        lines.append("")

    section("template", {key: value for key, value in schema.items() if key != "$defs"})
    for name, value in schema["$defs"].items():
        section(name, value)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for language, suffix in [("en", ""), ("zh-CN", ".zh-CN")]:
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
