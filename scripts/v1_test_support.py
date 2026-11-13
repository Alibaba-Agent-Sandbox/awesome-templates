"""Literal v1 test inputs; no old-format runtime admission is provided."""

import yaml


def resource(name="example", *, env=None, start=None, ready=None, services=None):
    template = {"image": "fixture/image:1", "cpu": 2, "memorySize": 2048}
    if start is not None: template["startCommand"] = start
    if ready is not None: template["readyCommand"] = ready
    return {"specVersion": 1, "name": name, "sandbox": {"agent": {"provider": "alicloud-express", "template": template}}}


def publication(source, name="example", version="1.0.1"):
    for file in ["README.md", "README.zh-CN.md"]:
        if not (source / file).exists():
            (source / file).write_text("Example\n")
    (source / "registry.yaml").write_text(
        yaml.safe_dump(
            {
                "specVersion": 1,
                "name": name,
                "version": version,
                "description": {"en": "Example", "zh": "示例"},
                "author": "example",
                "license": "Apache-2.0",
                "readme": {"en": "README.md", "zh": "README.zh-CN.md"},
            }
        )
    )
