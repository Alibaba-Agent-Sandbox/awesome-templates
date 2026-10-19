"""Verify source transfer and platform-step acceptance boundaries without cloud."""
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import pytest

import express_e2e as harness
from prepare_steps import BASE, ROOT, instructions, prepare


def fixture(tmp_path: Path, extra: str = "") -> Path:
    source = tmp_path / "source"
    source.mkdir()
    (source / "template.yaml").write_text("name: example\nversion: 1.0.0\n")
    (source / "commands.py").write_text("# actual source with 'quotes' and 中文\n")
    (source / "Dockerfile").write_text(BASE.join(["FROM ", "\n"]) +
        "ENV FIRST=one SECOND=\"two words\"\n" + extra +
        "WORKDIR /home/user/app\nCOPY commands.py .\nUSER user\nEXPOSE 9000\n")
    return source


def test_copy_step_recreates_exact_bytes_and_mode(tmp_path: Path):
    source = fixture(tmp_path)
    target = tmp_path / "restored"
    docker = source / "Dockerfile"
    docker.write_text(docker.read_text().replace("WORKDIR /home/user/app", f"WORKDIR {target}"))
    (source / "commands.py").chmod(0o640)
    manifest, proof = prepare(source)
    copy = next(step for step in manifest["build"]["steps"] if step["type"] == "RUN")
    subprocess.run(copy["args"][0], shell=True, check=True)
    assert (target / "commands.py").read_bytes() == (source / "commands.py").read_bytes()
    assert (target / "commands.py").stat().st_mode & 0o777 == 0o640
    assert proof["inputs_sha256"]["commands.py"]
    assert {"type": "ENV", "args": ["FIRST", "one", "SECOND", "two words"]} in manifest["build"]["steps"]


def test_heredoc_and_continuation_remain_executable():
    rows = instructions("RUN python3 - <<'PY'\nprint('hello')\nPY\nRUN echo one \\\n+ && echo two\nUSER user\n")
    assert rows[0] == ("RUN", "python3 - <<'PY'\nprint('hello')\nPY")
    result = subprocess.run(rows[0][1], shell=True, check=True, text=True, capture_output=True)
    assert result.stdout == "hello\n"
    assert "echo two" in rows[1][1]
    assert rows[-1] == ("USER", "user")


@pytest.mark.parametrize("extra", ["ADD public /app\n", "ARG UNPINNED\n", "COPY ../outside /app/\n", "COPY .env /app/\n"])
def test_unsupported_or_private_inputs_rejected(tmp_path: Path, extra: str):
    source = fixture(tmp_path, extra)
    (source / ".env").write_text("SECRET=placeholder")
    with pytest.raises(ValueError):
        prepare(source)


def test_all_catalog_profiles_generate_with_explicit_pins():
    for path in ROOT.glob("*/Dockerfile"):
        data, proof = prepare(path.parent, server_commit="e2cb27e24fde0a67112f82b8d44af463445a5d1a")
        assert data["build"]["steps"][-1] == {"type": "USER", "args": ["user"]}
        assert "<" not in data["base"]
        assert proof["inputs_sha256"]["Dockerfile"]
        assert "35da216a300f1e2e84254a1cf4b4a7ea98681505" not in json.dumps(data["build"])


@pytest.mark.parametrize("status", ["ready", {"state": "ready"}, '{"state":"ready"}', "{'state': 'ready'}"])
def test_ready_status_formats(status):
    assert harness.template_state({"status": status}) == "ready"


def test_submitted_requires_official_ready_readback(tmp_path: Path):
    options = harness.Options(tmp_path, [], "", "", 2, 20, 20, 20, 0, "owned", build_mode="steps")
    states = iter(["building", "ready"])
    calls = []
    def run(args, timeout):
        calls.append(args)
        return harness.Proc(0, json.dumps({"status": {"state": next(states)}}), "")
    with patch.object(harness.time, "sleep"):
        assert harness.wait_for_steps_ready("synthetic", options, run)
    assert len(calls) == 2
    assert all("--official-api" in args and "info" in args for args in calls)


@pytest.mark.parametrize("status", ["error", "unknown", "submitted-with-no-poll", ["ready"]])
def test_failed_or_unknown_state_cannot_pass(tmp_path: Path, status):
    options = harness.Options(tmp_path, [], "", "", 2, 20, 20, 20, 0, "owned", build_mode="steps")
    def run(*args):
        return harness.Proc(0, json.dumps({"status": status}), "")
    try:
        assert not harness.wait_for_steps_ready("synthetic", options, run)
    except ValueError:
        assert isinstance(status, list)
