"""Human field tables retain schema coverage without rendering nested schema JSON."""

import json
from pathlib import Path

import pytest
from check_docs import check_file
from sync_template_reference import Reference, generate

ROOT = Path(__file__).resolve().parents[1]


def declared_fields(value, pointer=""):
    result = set()
    if isinstance(value, dict):
        result.update(
            pointer + "/properties/" + name for name in value.get("properties", {})
        )
        for key, child in value.items():
            if (
                key != "if"
            ):  # Conditions select an existing field, not a new input shape.
                result.update(declared_fields(child, pointer + "/" + key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            result.update(declared_fields(child, pointer + "/" + str(index)))
    return result


@pytest.mark.parametrize("language,suffix", [("en", ""), ("zh-CN", ".zh-CN")])
def test_complete_readable_field_tables(language, suffix):
    schema = json.loads((ROOT / "spec/template-v1.schema.json").read_text())
    contract = json.loads((ROOT / "contracts/template-v1/contract.json").read_text())
    reference = Reference(schema, contract, language)
    text = reference.render()
    assert reference.covered_fields == declared_fields(schema)
    assert text == generate(language)
    assert text == (ROOT / f"docs/template-fields{suffix}.md").read_text()
    assert check_file(ROOT / f"docs/template-fields{suffix}.md") == []
    assert (
        '"properties"' not in text and '"oneOf"' not in text and '"allOf"' not in text
    )
    assert (
        "object · [fields](#field-sandbox)" in text
        if language == "en"
        else "#field-sandbox" in text
    )
    assert "#type-positiveintegerinput" in text
    assert (
        "#type-instance_opensandbox" not in text
    )  # Explicit anchors are normalized consistently.
    assert "#type-instance-opensandbox" in text
    assert "maxRunSeconds" in text and "`600`" in text
    assert "type=custom" in text and "type=serverless-devs" in text
    assert max(len(line) for line in text.splitlines() if line.startswith("|")) < 600
