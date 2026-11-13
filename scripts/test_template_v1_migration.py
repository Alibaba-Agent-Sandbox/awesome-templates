"""One-time public-format migration preserves original workload and test declarations."""

import json
from pathlib import Path

import yaml
from template_application import (
    engineering_checks,
    normalize_manifest,
    project_manifest,
)

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = json.loads(
    (
        ROOT / "scripts/fixtures/migrations/20261112-original-declarations.json"
    ).read_text()
)


def test_all_original_workloads_and_engineering_assertions_survive():
    assert len(ORIGINAL) == 48
    for name, old in ORIGINAL.items():
        source = ROOT / name
        data = yaml.safe_load((source / "template.yaml").read_text())
        normalized = normalize_manifest(data)
        projected = project_manifest(data, source)
        assert data["specVersion"] == 1 and "spec_version" not in data
        assert data["name"] == ("example" if name == "_skeleton" else old["name"])
        assert {key: engineering_checks(name)[key] for key in ["smoke", "priority", "wave"] if key in engineering_checks(name)} == {
            key: old[key] for key in ["smoke", "priority", "wave"] if key in old
        }
        assert projected["base"] == old["base"]
        assert projected["resources"] == old["resources"]
        assert projected["start_cmd"] == old["start_cmd"]
        assert projected["ready_cmd"] == old["ready_cmd"]
        assert projected["provides"] == old["provides"]
        assert projected["ports"] == sorted(set(old["ports"]))
        if name != "agents-api":
            assert {key: projected["env"].get(key) for key in old["env"]} == old["env"]
            assert data["sandbox"]["agent"]["provider"] == "alicloud-express"
            assert "instance" not in data["sandbox"]["agent"]
            assert "startCommand" not in data["sandbox"]["agent"]["template"]
            import ast
            tree = ast.parse((source / "run.py").read_text())
            assignments = {node.targets[0].id: ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id == "START_COMMAND"}
            assert assignments["START_COMMAND"] == old["start_cmd"]
        else:
            assert "application" not in data and "deployment" not in data
            assert data["serving"]
        for key in ["aliases", "build_profiles"]:
            if key in old:
                assert projected[key] == old[key]
        for key in [
            "smoke",
            "priority",
            "wave",
            "base",
            "generation",
            "version",
            "description",
            "tags",
            "author",
            "license",
        ]:
            assert key not in data


def test_catalog_locators_have_one_metadata_authority():
    catalog = yaml.safe_load((ROOT / "awesome-templates.yaml").read_text())
    assert catalog["schema_version"] == 3 and len(catalog["templates"]) == 47
    for row in catalog["templates"]:
        assert set(row) == {"name", "path", "repo", "status", "registry"}
        assert row["registry"] == row["path"] + "/registry.yaml"
        metadata = yaml.safe_load((ROOT / row["registry"]).read_text())
        assert metadata["name"] == row["name"]
        for language in ["en", "zh"]:
            assert metadata["description"][language]
            readme = ROOT / row["path"] / metadata["readme"][language]
            assert readme.is_file()


def test_each_declared_configuration_name_is_documented_in_both_languages():
    import re

    for name in ORIGINAL:
        source = ROOT / name
        text = (source / "template.yaml").read_text()
        data = yaml.safe_load(text)
        names = set(ORIGINAL[name].get("env", {}))
        names.update(re.findall(r"\$\{env\('([^']+)'\)\}", text))
        for filename in ["README.md", "README.zh-CN.md"]:
            readme = (source / filename).read_text()
            assert names <= {key for key in names if key in readme}, (
                name,
                filename,
                sorted(key for key in names if key not in readme),
            )
