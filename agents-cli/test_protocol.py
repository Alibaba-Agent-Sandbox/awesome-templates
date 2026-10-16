"""Real HTTP/adapter protocol regressions with an explicitly selected fixture PATH.

These fixtures are synthetic protocol tests, never upstream/model acceptance.
Both production startup forms must enforce the same closed endpoint policy.
"""
from __future__ import annotations

from contextlib import contextmanager
import importlib.util
import os
from pathlib import Path
import secrets
import shlex
import socket
import subprocess
import sys
import time

import httpx
import pytest
import yaml

HERE = Path(__file__).resolve().parent


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@contextmanager
def running_server(tmp_path: Path, canonical: bool, fixtures: bool = True):
    port = free_port()
    token = secrets.token_hex(24)
    env = {name: value for name, value in os.environ.items() if not any(
        part in name.upper() for part in ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL"))}
    for name in ("ABX_SERVER_POLICY", "ABX_SERVER_POLICY_FILE", "CODEX_HOME"):
        env.pop(name, None)
    env.update(ABX_SERVER_PORT=str(port), ABX_PTY_PORT=str(free_port()),
               ABX_SERVER_TOKEN=token, ABX_SERVER_BASE_DIR=str(tmp_path),
               WORKSPACE=str(tmp_path), E2E_RUN_LLM="0")
    if fixtures:
        env["PATH"] = str(HERE / "e2e-bin") + os.pathsep + env.get("PATH", "")
    if canonical:
        start_command = yaml.safe_load((HERE / "template.yaml").read_text())["start_cmd"]
        template_argv = shlex.split(start_command.replace("/home/user/app", str(HERE)))
        assert template_argv[0] == "agent-sandbox-server"
        argv = [sys.executable, "-m", "agent_sandbox.server", *template_argv[1:],
                "--host", "127.0.0.1", "--port", str(port)]
    else:
        argv = [sys.executable, str(HERE / "commands.py")]
    # In-memory/local secrets and upstream diagnostics never reach test output.
    process = subprocess.Popen(argv, cwd=tmp_path, env=env, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, start_new_session=True)
    try:
        with httpx.Client(base_url=f"http://127.0.0.1:{port}",
                          headers={"Authorization": "Bearer " + token}, timeout=10) as client:
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    pytest.fail("test HTTP server exited before readiness")
                try:
                    if client.get("/health").status_code == 200:
                        break
                except httpx.TransportError:
                    pass
                time.sleep(.05)
            else:
                pytest.fail("test HTTP server did not become healthy")
            yield client, token
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


@pytest.mark.parametrize("canonical", [False, True])
def test_authenticated_allowlist_has_no_policy_escape(tmp_path, canonical):
    with running_server(tmp_path, canonical) as (client, token):
        for auth in ({}, {"Authorization": "Bearer synthetic-wrong-token"}):
            response = httpx.get(str(client.base_url).rstrip("/") + "/commands", headers=auth, timeout=5)
            assert response.status_code == 401
            assert token not in response.text
        assert client.get("/commands").status_code == 200
        assert client.post("/commands/agents_version", json={}).json() == {
            "result": "codex 0.162.1; qwen-code 0.23.0"}
        for method, path in (("POST", "/shell"), ("GET", "/files"),
                             ("POST", "/files/upload-stream"),
                             ("GET", "/files/download-stream"),
                             ("POST", "/process/start"), ("GET", "/v1/models"),
                             ("POST", "/v1/agents/responses"),
                             ("POST", "/v1/agents/definitions")):
            response = client.request(method, path, json={} if method == "POST" else None)
            assert response.status_code == 404, (method, path)
            assert token not in response.text
        response = client.post("/v1/agents/sessions", json={"adapter": "claude-code"})
        assert response.status_code == 404


def message_texts(payload: dict) -> list[str]:
    return [str(part["text"]) for item in payload.get("data", []) if item.get("type") == "message"
            for part in item.get("content", []) if part.get("text")]


@pytest.mark.parametrize("canonical", [False, True])
def test_explicit_fixture_path_runs_both_adapters_and_repeated_turns(tmp_path, canonical):
    with running_server(tmp_path, canonical) as (client, _):
        for adapter, expected in (("codex", "hello-from-fake-codex"), ("qwen-code", "hello-from-fake-qwen")):
            response = client.post("/v1/agents/sessions", json={
                "adapter": adapter,
                "agent": {"model": adapter},
                "environment": {"type": "self_hosted", "workspace_directory": str(tmp_path)},
            })
            assert response.status_code == 200
            assert response.headers.get("X-Agent-Sandbox-Local") == "1"
            session = response.json()["id"]
            for turn in (1, 2):
                response = client.post(f"/v1/agents/sessions/{session}/events", json={"events": [{
                    "type": "agent.session.input.message",
                    "input": [{"role": "user", "content": [{"type": "input_text", "text": "protocol fixture turn"}]}],
                }]})
                assert response.status_code == 202
                deadline = time.monotonic() + 10
                while time.monotonic() < deadline:
                    response = client.get(f"/v1/agents/sessions/{session}/items?limit=100&order=asc")
                    assert response.status_code == 200
                    if message_texts(response.json()).count(expected) >= turn:
                        break
                    time.sleep(.05)
                else:
                    pytest.fail("synthetic adapter turn did not complete")
            assert client.get(f"/v1/agents/sessions/{session}").status_code == 200


def test_disabled_model_flag_does_not_select_fixture_path(monkeypatch):
    monkeypatch.setenv("E2E_RUN_LLM", "0")
    before = os.environ.get("PATH", "")
    spec = importlib.util.spec_from_file_location("agents_cli_commands", HERE / "commands.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert os.environ.get("PATH", "") == before


@pytest.mark.parametrize("failure", ["exit", "wrong-version", "timeout"])
def test_diagnostic_errors_omit_raw_cli_output_and_timeout_argv(monkeypatch, failure):
    spec = importlib.util.spec_from_file_location("agents_cli_diagnostic", HERE / "commands.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    private = "synthetic-private-upstream-output"
    monkeypatch.setattr(module.shutil, "which", lambda name: "/synthetic/bin/" + name)
    def run(argv, **kwargs):
        assert kwargs["timeout"] == 20
        if failure == "timeout":
            raise subprocess.TimeoutExpired([*argv, private], 20)
        return subprocess.CompletedProcess(argv, int(failure == "exit"), private, private)
    monkeypatch.setattr(module.subprocess, "run", run)
    with pytest.raises(RuntimeError) as exc:
        module.agents_version()
    import traceback
    assert private not in "".join(traceback.format_exception(exc.value))


@pytest.mark.parametrize("canonical", [False, True])
def test_real_diagnostics_do_not_fall_back_to_fixtures_when_cli_missing(tmp_path, canonical, monkeypatch):
    # Keep Python launch absolute and hide every upstream CLI. E2E_RUN_LLM=0
    # must not prepend the repository's synthetic binaries behind our back.
    empty = tmp_path / "empty-bin"
    empty.mkdir()
    monkeypatch.setenv("PATH", str(empty))
    with running_server(tmp_path, canonical, fixtures=False) as (client, _):
        response = client.post("/commands/agents_version", json={})
        assert response.status_code == 500
        assert response.json().get("type") == "RuntimeError"
        assert "codex is missing" in response.json().get("error", "")
