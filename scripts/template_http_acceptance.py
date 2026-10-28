"""Run unchanged template HTTP controllers with required non-model fixtures.

These fixtures authorize only owned test resources. They never borrow an
operator's vendor/model credentials and are separate from image build inputs.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from urllib.parse import urlsplit
from pathlib import Path
import secrets
import sys
import yaml

from express_e2e import run_monitored


def fixture_environment(name: str, *, real_usage: bool = False) -> tuple[dict[str, str], dict[str, str], dict]:
    server, controller, proof = {}, {}, {"model_credentials_injected": False}
    if name == "openclaw":
        token = secrets.token_urlsafe(32)
        server["OPENCLAW_GATEWAY_TOKEN"] = token
        controller["OPENCLAW_GATEWAY_TOKEN"] = token
        proof.update(gateway_lifecycle_required=True, generated_test_token=True)
    elif name == "cursor-agent" and not real_usage:
        server["CURSOR_API_KEY"] = "key_" + "a" * 64
        controller.update(E2E_CURSOR_INVALID_KEY_FIXTURE="1", E2E_REMOTE_SANDBOX="1")
        proof.update(native_authentication_error_path_required=True,
                     synthetic_invalid_vendor_credential=True)
    elif name == "devin" and not real_usage:
        controller.update(E2E_DEVIN_NO_ACCOUNT_FIXTURE="1", E2E_REMOTE_SANDBOX="1")
        proof.update(native_authentication_error_path_required=True,
                     credential_absence_required=True)
    elif name == "osworld":
        controller.update(E2E_RUN_DESKTOP="1", E2E_REQUIRE_DESKTOP="1")
        proof["desktop_lifecycle_required"] = True
    return server, controller, proof


def controller_environment(source: Path, urls: dict[int, str], fixture: dict[str, str], *, token: str | None = None, gateway_headers: dict[str, str] | None = None, real_usage: bool = False, owned_sandbox_id: str | None = None) -> dict[str, str]:
    if gateway_headers is not None and (not isinstance(gateway_headers, dict) or any(
            not isinstance(key, str) or not isinstance(value, str) or not key or '\r' in key + value or '\n' in key + value
            for key, value in gateway_headers.items())):
        raise ValueError("gateway_headers must be an object of string HTTP headers")
    if token and any(key.lower() == 'authorization' for key in gateway_headers or {}):
        raise ValueError("gateway and application Authorization cannot overwrite one another")
    # An allowlist prevents unrelated operator keys/config from reaching tests.
    env = {key: value for key, value in os.environ.items()
           if key in {"PATH", "LANG", "LC_ALL", "SYSTEMROOT", "TMPDIR", "PYTHONPATH",
                      "SSL_CERT_FILE", "SSL_CERT_DIR"}}
    env.update(E2E_BASE_URL=urls[9000], E2E_BASE_DIR="/home/user/app",
               E2E_WORKSPACE="/home/user/app", E2E_RUN_LLM="0", E2E_REQUIRE_LLM="0",
               E2E_REQUIRE_CLI="1", E2E_REQUIRE_OCR="1", E2E_REQUIRE_DATABASES="1",
               E2E_REQUIRE_TOOLCHAIN="1")
    manifest_path = source / "template.yaml"
    if manifest_path.is_file():
        manifest = yaml.safe_load(manifest_path.read_text())
        workspace = manifest.get("env", {}).get("WORKSPACE", "/home/user/app")
        if not isinstance(workspace, str) or not workspace.startswith("/"):
            raise ValueError("controller WORKSPACE must be an absolute runtime path")
        env["E2E_WORKSPACE"] = workspace
    if real_usage:
        env.update(E2E_RUN_LLM="1", E2E_REQUIRE_LLM="1", E2E_REQUIRE_DOCUMENT="1",
                   E2E_REQUIRE_MEDIA="1", E2E_RUN_DESKTOP="1", E2E_REQUIRE_DESKTOP="1",
                   E2E_REMOTE_SANDBOX="1")
        # These select test tasks and deadlines, never operator credentials.
        for key in {"E2E_MODEL", "E2E_LLM_TIMEOUT", "E2E_COMMAND_TIMEOUT", "E2E_MAX_TURNS"}:
            if key in os.environ:
                env[key] = os.environ[key]
    if owned_sandbox_id is not None:
        if not real_usage or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", owned_sandbox_id):
            raise ValueError("owned controller target requires real usage and a valid created sandbox ID")
        target = urls[9000].rstrip("/")
        parts = urlsplit(target)
        if (parts.scheme not in {"http", "https"} or not parts.hostname
                or parts.username or parts.password or parts.fragment
                or "/sandboxes/" in parts.path and not parts.path.rstrip("/").endswith(
                    "/sandboxes/" + owned_sandbox_id + "/proxy/9000")):
            raise ValueError("controller target must match its created sandbox endpoint")
        env.update(E2E_OWNED_SANDBOX_ID=owned_sandbox_id, E2E_OWNED_GATEWAY_URL=target)
    if source.name == "code-server":
        env["E2E_CODE_SERVER_URL"] = urls[8443]
    if source.name == "next-app":
        env.update(E2E_NEXT_URL=urls[3000], E2E_VITE_URL=urls[5173])
    if source.name == "chrome":
        env.update(E2E_CHROME_CDP_URL=urls[9222], E2E_CHROME_VNC_URL=urls[6080],
                   E2E_WORKSPACE="/home/user/workspace", E2E_REQUIRE_CHROME="1")
    allowed = {"E2E_CURSOR_INVALID_KEY_FIXTURE", "E2E_DEVIN_NO_ACCOUNT_FIXTURE",
               "E2E_REMOTE_SANDBOX", "E2E_RUN_DESKTOP", "E2E_REQUIRE_DESKTOP"}
    if source.name == "openclaw":
        allowed.add("OPENCLAW_GATEWAY_TOKEN")
    if set(fixture) - allowed:
        raise ValueError("only owned non-model controller fixtures are accepted")
    env.update(fixture)
    env["E2E_GATEWAY_HEADERS_JSON"] = json.dumps(gateway_headers or {})
    if token is not None:
        env["ABX_SERVER_TOKEN"] = token
    return env


def run_controller(source: Path, urls: dict[int, str], private: Path,
                   fixture: dict[str, str], *, token: str | None = None, gateway_headers: dict[str, str] | None = None, real_usage: bool = False, owned_sandbox_id: str | None = None) -> dict:
    script = source / "e2e_test.py"
    transport = Path(__file__).with_name("template_controller_transport.py")
    verifier_bytes, transport_bytes = script.read_bytes(), transport.read_bytes()
    dependencies = {name: (source / name).read_bytes() for name in
                    ("http_model_e2e.py", "model_e2e_test.py", "model_fixture.py")
                    if source.name in {"browser-use", "stagehand"} and (source / name).is_file()}
    result = run_monitored([sys.executable, str(transport), str(script)],
                           env=controller_environment(source, urls, fixture, token=token, gateway_headers=gateway_headers, real_usage=real_usage, owned_sandbox_id=owned_sandbox_id),
                           idle_timeout=900 if real_usage else 600, wall_timeout=1800 if real_usage else 900)
    (private / "http.log").write_text(result.stdout + "\n" + result.stderr)
    lines = (result.stdout + "\n" + result.stderr).splitlines()
    counts = {"exit_code": result.returncode,
              "pass_count": sum(line.startswith("[PASS]") for line in lines),
              "fail_count": sum(line.startswith("[FAIL]") for line in lines),
              "skip_count": sum(line.startswith("[SKIP]") for line in lines),
              "not_run_count": sum(line.startswith("[NOT RUN]") for line in lines),
              "verifier_sha256": hashlib.sha256(verifier_bytes).hexdigest()}
    counts["created_sandbox_target_bound"] = owned_sandbox_id is not None
    counts["transport_adapter_sha256"] = hashlib.sha256(transport_bytes).hexdigest()
    counts["verifier_inputs_unchanged"] = script.read_bytes() == verifier_bytes and transport.read_bytes() == transport_bytes
    if dependencies:
        counts["verifier_dependencies_sha256"] = {name: hashlib.sha256(data).hexdigest() for name, data in dependencies.items()}
        counts["verifier_inputs_unchanged"] = counts["verifier_inputs_unchanged"] and all(
            (source / name).is_file() and (source / name).read_bytes() == data for name, data in dependencies.items())
    complete = result.returncode == 0 and counts["pass_count"] > 0 and not counts["fail_count"] and counts["verifier_inputs_unchanged"]
    if real_usage:
        complete = complete and not counts["skip_count"] and not counts["not_run_count"]
        counts["real_usage_required"] = True
    if source.name in {"cursor-agent", "devin"}:
        complete = complete and not counts["skip_count"] and counts["pass_count"] >= 16
    if source.name == "osworld":
        complete = complete and not counts["skip_count"] and counts["pass_count"] >= 18
    if source.name == "chrome":
        complete = complete and not counts["skip_count"]
    if source.name == "openclaw":
        complete = complete and bool(fixture.get("OPENCLAW_GATEWAY_TOKEN")) and not any(
            line.startswith("[SKIP] real gateway lifecycle") for line in lines)
    counts["passed"] = bool(complete)
    return counts
