"""Run unchanged template HTTP controllers with required non-model fixtures.

These fixtures authorize only owned test resources. They never borrow an
operator's vendor/model credentials and are separate from image build inputs.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import secrets
import sys

from express_e2e import run_monitored


def fixture_environment(name: str) -> tuple[dict[str, str], dict[str, str], dict]:
    server, controller, proof = {}, {}, {"model_credentials_injected": False}
    if name == "openclaw":
        token = secrets.token_urlsafe(32)
        server["OPENCLAW_GATEWAY_TOKEN"] = token
        controller["OPENCLAW_GATEWAY_TOKEN"] = token
        proof.update(gateway_lifecycle_required=True, generated_test_token=True)
    elif name == "cursor-agent":
        server["CURSOR_API_KEY"] = "key_" + "a" * 64
        controller.update(E2E_CURSOR_INVALID_KEY_FIXTURE="1", E2E_REMOTE_SANDBOX="1")
        proof.update(native_authentication_error_path_required=True,
                     synthetic_invalid_vendor_credential=True)
    elif name == "devin":
        controller.update(E2E_DEVIN_NO_ACCOUNT_FIXTURE="1", E2E_REMOTE_SANDBOX="1")
        proof.update(native_authentication_error_path_required=True,
                     credential_absence_required=True)
    elif name == "osworld":
        controller.update(E2E_RUN_DESKTOP="1", E2E_REQUIRE_DESKTOP="1")
        proof["desktop_lifecycle_required"] = True
    return server, controller, proof


def controller_environment(source: Path, urls: dict[int, str], fixture: dict[str, str]) -> dict[str, str]:
    # An allowlist prevents unrelated operator keys/config from reaching tests.
    env = {key: value for key, value in os.environ.items()
           if key in {"PATH", "LANG", "LC_ALL", "SYSTEMROOT", "TMPDIR", "PYTHONPATH",
                      "SSL_CERT_FILE", "SSL_CERT_DIR"}}
    env.update(E2E_BASE_URL=urls[9000], E2E_BASE_DIR="/home/user/app",
               E2E_WORKSPACE="/home/user/app", E2E_RUN_LLM="0", E2E_REQUIRE_LLM="0",
               E2E_REQUIRE_CLI="1", E2E_REQUIRE_OCR="1", E2E_REQUIRE_DATABASES="1",
               E2E_REQUIRE_TOOLCHAIN="1")
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
    return env


def run_controller(source: Path, urls: dict[int, str], private: Path,
                   fixture: dict[str, str]) -> dict:
    script = source / "e2e_test.py"
    result = run_monitored([sys.executable, str(script)],
                           env=controller_environment(source, urls, fixture),
                           idle_timeout=600, wall_timeout=900)
    (private / "http.log").write_text(result.stdout + "\n" + result.stderr)
    lines = (result.stdout + "\n" + result.stderr).splitlines()
    counts = {"exit_code": result.returncode,
              "pass_count": sum(line.startswith("[PASS]") for line in lines),
              "fail_count": sum(line.startswith("[FAIL]") for line in lines),
              "skip_count": sum(line.startswith("[SKIP]") for line in lines),
              "verifier_sha256": hashlib.sha256(script.read_bytes()).hexdigest()}
    complete = result.returncode == 0 and counts["pass_count"] > 0 and not counts["fail_count"]
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
