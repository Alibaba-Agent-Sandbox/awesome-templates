"""Verify source transfer and platform-step acceptance boundaries without cloud."""
import json
import io
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import pytest

import express_e2e as harness
import prepare_steps
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
        selected = (prepare_steps.pinned_server_commit(path.parent) if (path.parent / "server-sdk.commit").exists()
                    else "e2cb27e24fde0a67112f82b8d44af463445a5d1a")
        data, proof = prepare(path.parent, server_commit=selected)
        assert data["build"]["steps"][-1] == {"type": "USER", "args": ["user"]}
        assert "<" not in data["base"]
        assert proof["inputs_sha256"]["Dockerfile"]
        assert proof["server_commit_override"] == selected
        assert proof["steps_json_bytes"] <= 15000


def test_immutable_source_fetch_checks_bytes_before_publication(tmp_path: Path):
    import shlex
    import tarfile
    from types import SimpleNamespace
    import urllib.request
    source = fixture(tmp_path)
    data = (source / "commands.py").read_bytes()
    target = tmp_path / "restored.py"
    with patch.object(prepare_steps.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout=data)):
        command, _ = prepare_steps._copy(source, "commands.py " + str(target), "/", "a" * 40)
    code = shlex.split(command)[2]
    code = code.replace("/tmp/abx-step-source-", str(tmp_path / "source-cache-"))
    def archive(content):
        output = io.BytesIO()
        with tarfile.open(fileobj=output, mode="w:gz") as tar:
            entry = tarfile.TarInfo("awesome-templates-" + "a" * 40 + "/source/commands.py")
            entry.size = len(content)
            tar.addfile(entry, io.BytesIO(content))
        return output.getvalue()
    with patch.object(urllib.request, "urlopen", return_value=io.BytesIO(archive(data))):
        exec(code, {})
    assert target.read_bytes() == data
    target.unlink()
    for cache in tmp_path.glob("source-cache-*"):
        cache.unlink()
    with patch.object(urllib.request, "urlopen", return_value=io.BytesIO(archive(b"changed upstream bytes"))):
        with pytest.raises(RuntimeError, match="integrity mismatch"):
            exec(code, {})
    assert not target.exists()


def test_oversized_random_copy_cannot_reach_cloud(tmp_path: Path):
    source = fixture(tmp_path)
    (source / "commands.py").write_bytes(os.urandom(50000))
    with pytest.raises(ValueError, match="16 KiB"):
        prepare(source)


def test_run_uses_declared_path_without_native_env_propagation(tmp_path: Path):
    binary = tmp_path / "bin"
    binary.mkdir()
    tool = binary / "abx-declared-tool"
    tool.write_text("#!/bin/sh\nprintf DECLARED_PATH_OK\n")
    tool.chmod(0o755)
    source = fixture(tmp_path, f'ENV PATH="{binary}:${{PATH}}"\nRUN abx-declared-tool\n')
    manifest, _ = prepare(source)
    first_run = next(step for step in manifest["build"]["steps"] if step["type"] == "RUN")
    result = subprocess.run(first_run["args"][0], shell=True, text=True, capture_output=True, check=True)
    assert result.stdout == "DECLARED_PATH_OK"
    path_step = [step for step in manifest["build"]["steps"] if step["type"] == "ENV"][-1]
    assert path_step["args"][0] == "PATH"
    assert "${PATH}" not in path_step["args"][1]
    assert path_step["args"][1].startswith(str(binary) + ":")


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
    assert all(args[:3] == ["--json", "template", "info"] and args[-1] == "synthetic" for args in calls)


@pytest.mark.parametrize("status", ["error", "unknown", "submitted-with-no-poll", ["ready"]])
def test_failed_or_unknown_state_cannot_pass(tmp_path: Path, status):
    options = harness.Options(tmp_path, [], "", "", 2, 20, 20, 20, 0, "owned", build_mode="steps")
    def run(*args):
        return harness.Proc(0, json.dumps({"status": status}), "")
    try:
        assert not harness.wait_for_steps_ready("synthetic", options, run)
    except ValueError:
        assert isinstance(status, list)


def test_explicit_template_server_pin_rejects_a_stale_step_override(tmp_path):
    import hashlib
    source=fixture(tmp_path)
    pin='f'*40
    (source/'server-sdk.commit').write_text(pin+'\n')
    dockerfile=source/'Dockerfile'
    dockerfile.write_text(dockerfile.read_text().replace('USER user\n', f'RUN pip install "agent-sandbox-server @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/{pin}.tar.gz#subdirectory=server-sdk"\nUSER user\n'))
    with pytest.raises(ValueError,match='required template'):
        prepare(source,server_commit='e'*40)
    _,proof=prepare(source,server_commit=pin)
    assert proof['template_server_commit']==pin
    assert proof['inputs_sha256']['server-sdk.commit']==hashlib.sha256((pin+'\n').encode()).hexdigest()


def test_preparation_binds_complete_source_manifest_excluding_only_qualification(tmp_path):
    from manifest_contract import manifest_contract_sha256
    source=fixture(tmp_path)
    _,proof=prepare(source)
    assert proof['source_manifest_contract_sha256']==manifest_contract_sha256((source/'template.yaml').read_bytes())
    original=proof['source_manifest_contract_sha256']
    path=source/'template.yaml';path.write_text(path.read_text()+'tested_on: [alicloud-express]\n')
    assert prepare(source)[1]['source_manifest_contract_sha256']==original
    path.write_text(path.read_text()+'start_cmd: changed\n')
    assert prepare(source)[1]['source_manifest_contract_sha256']!=original
