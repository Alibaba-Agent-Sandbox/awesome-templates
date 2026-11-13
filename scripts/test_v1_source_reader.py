"""Actual public source file paths use the shared Core reader before schema consumers."""

import json
import shutil
from pathlib import Path

import check_template
import pytest
from select_image_templates import catalog_names
from template_application import load_source_document, publication_metadata

ROOT = Path(__file__).resolve().parents[1]
VECTORS = json.loads((ROOT / "contracts/template-v1/yaml-fixtures.json").read_text())


@pytest.mark.parametrize("case", VECTORS["valid"], ids=lambda case: case["id"])
def test_valid_public_file_inputs(tmp_path, case):
    path = tmp_path / "template.yaml"
    path.write_bytes(case["text"].encode("utf-8"))
    assert load_source_document(path) == case["expected"]


@pytest.mark.parametrize("case", VECTORS["invalid"], ids=lambda case: case["id"])
def test_invalid_public_file_inputs_are_safe(tmp_path, case):
    source = (
        case["text"].encode("utf-8")
        if "text" in case
        else bytes.fromhex(case["hex"])
        if "hex" in case
        else (case["repeat"] * case["count"]).encode("utf-8")
    )
    path = tmp_path / "template.yaml"
    path.write_bytes(source)
    with pytest.raises((ValueError, TypeError)) as error:
        load_source_document(path)
    assert "private-source-canary" not in str(error.value)
    assert path.read_bytes() == source


def test_checker_metadata_and_catalog_preserve_core_strings_without_env(
    tmp_path, monkeypatch
):
    source = tmp_path / "_skeleton"
    shutil.copytree(ROOT / "_skeleton", source)
    path = source / "template.yaml"
    path.write_text(
        path.read_text() + "\nvars:\n  FLAG: on\n  WHEN: 2026-11-12\n"
    )
    monkeypatch.setenv("FLAG", "must-not-be-read")
    data, errors = check_template._load_yaml(path)
    assert errors == []
    assert data["vars"]["FLAG"] == "on"
    assert data["vars"]["WHEN"] == "2026-11-12"
    (source / "registry.yaml").write_text(
        "specVersion: 1\nname: example\nversion: 1.0.0\ndescription: {en: on, zh: 2026-11-12}\nauthor: on\nlicense: Apache-2.0\ntags: [on]\nreadme: {en: README.md, zh: README.zh-CN.md}\n"
    )
    metadata = publication_metadata(source, data)
    assert metadata["author"] == "on" and metadata["description"] == {
        "en": "on",
        "zh": "2026-11-12",
    }
    assert check_template.check_directory(source) == []
    (tmp_path / "awesome-templates.yaml").write_text(
        "schema_version: 3\ntemplates:\n  - {name: on, path: on, repo: example/repo, registry: on/registry.yaml, status: experimental}\n"
    )
    assert catalog_names(tmp_path) == ["on"]
