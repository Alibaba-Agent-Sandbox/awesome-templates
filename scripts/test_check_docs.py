"""Exercise document links, fragments and checkout ownership on real files."""
from pathlib import Path

from check_docs import check_file


def test_relative_fragment_encoded_path_and_reference_link(tmp_path: Path):
    (tmp_path / "two words.md").write_text("# Hello, world!\n## Hello, world!\n")
    doc = tmp_path / "README.md"
    doc.write_text("[first](two%20words.md#hello-world)\n[second][ref]\n[ref]: <two%20words.md#hello-world-1>\n")
    assert check_file(doc, tmp_path) == []


def test_broken_files_fragments_and_repository_escape_are_errors(tmp_path: Path):
    doc = tmp_path / "README.md"
    doc.write_text("# Actual\n[missing](missing.md)\n[fragment](#absent)\n[outside](../private.md)\n")
    errors = check_file(doc, tmp_path)
    assert len(errors) == 3
    assert "missing local target" in errors[0]
    assert "missing heading" in errors[1]
    assert "leaves repository" in errors[2]


def test_examples_and_external_links_do_not_trigger_io(tmp_path: Path):
    doc = tmp_path / "README.md"
    doc.write_text("[online](https://example.invalid/path)\n`[inline](absent.md)`\n"
                   "```markdown\n[fenced](also-absent.md)\n```\n"
                   "~~~text\n[another](none.md)\n~~~\n")
    assert check_file(doc, tmp_path) == []


def test_chinese_heading_and_html_anchor(tmp_path: Path):
    doc = tmp_path / "README.md"
    doc.write_text('# 快速开始（CLI）\n<a id="custom"></a>\n[中文](#快速开始cli)\n[anchor](#custom)\n')
    assert check_file(doc, tmp_path) == []
