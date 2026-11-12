"""Literal v1 test inputs; no old-format runtime admission is provided."""

import yaml


def resource(name="example", *, env=None, start=None, ready=None, services=None):
    sandbox = {
        "provider": "alicloud-express",
        "template": {"image": "fixture/image:1", "props": {"cpu": 2, "memory": 2048}},
    }
    if env is not None:
        sandbox["instance"] = {"envs": env}
    if start is not None:
        sandbox["start"] = start
    if ready is not None:
        sandbox["ready"] = ready
    if services is not None:
        sandbox["services"] = services
    return {"specVersion": 1, "name": name, "sandbox": sandbox}


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
