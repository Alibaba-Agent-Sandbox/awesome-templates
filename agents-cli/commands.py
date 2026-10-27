"""Pinned Codex/Qwen Agents API with an explicit endpoint allowlist.

Synthetic CLIs belong to protocol tests and are never selected here.
"""
from __future__ import annotations

import os
import json
from pathlib import Path
import shutil
import subprocess
from urllib.parse import urlsplit

from agent_sandbox.server import ServerPolicy, command, start

_HERE = Path(__file__).resolve().parent
POLICY = ServerPolicy.from_file(str(_HERE / "server-policy.json"))
VERSIONS = {"codex": "0.162.1", "qwen": "0.23.0"}


@command("agents_configure_codex", description="Explicitly prepare a native Responses provider profile from startup model settings, without writing its key.")
def agents_configure_codex() -> dict:
    if not os.environ.get("OPENAI_API_KEY", "").strip():
        raise ValueError("OPENAI_API_KEY is required in the startup environment")
    base = os.environ.get("OPENAI_BASE_URL", "").strip()
    endpoint = urlsplit(base)
    if (len(base) > 2048 or endpoint.scheme not in {"https", "http"} or not endpoint.hostname
            or endpoint.username or endpoint.password or endpoint.query or endpoint.fragment):
        raise ValueError("OPENAI_BASE_URL must be an explicit HTTP(S) API base without credentials/query/fragment")
    home = Path(os.environ.get("CODEX_HOME", "/home/user/.codex"))
    if not home.is_absolute() or home.is_symlink():
        raise ValueError("CODEX_HOME must be an absolute nonsymlink directory")
    home.mkdir(mode=0o700, parents=True, exist_ok=True)
    config = home / "config.toml"
    text = ('model_provider = "owned_compatible"\n'
            '[model_providers.owned_compatible]\n'
            'name = "Explicit compatible endpoint"\n'
            'base_url = ' + json.dumps(base.rstrip('/')) + '\n'
            'env_key = "OPENAI_API_KEY"\n'
            'wire_api = "responses"\n'
            'supports_websockets = false\n')
    if config.is_symlink():
        raise ValueError("refusing a symlinked Codex config")
    try:
        descriptor = os.open(config, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    except FileExistsError:
        if not config.is_file() or config.stat().st_size > 8192 or config.read_text() != text:
            raise ValueError("existing Codex config differs; preserve it and launch with a new CODEX_HOME") from None
    else:
        with os.fdopen(descriptor, "w") as stream:
            stream.write(text)
    return {"configured": True, "wire_api": "responses", "credential_written": False}


@command("agents_version", description="Check both pinned CLI versions without a model call.")
def agents_version() -> str:
    for binary, expected in VERSIONS.items():
        executable = shutil.which(binary)
        if executable is None:
            raise RuntimeError(f"{binary} is missing; rebuild the pinned template")
        try:
            result = subprocess.run([executable, "--version"], capture_output=True,
                                    text=True, timeout=20, check=False)
        except (OSError, subprocess.TimeoutExpired):
            raise RuntimeError(f"{binary} version check failed") from None
        # Raw CLI output can contain local paths or credentials.
        if result.returncode != 0 or result.stdout.strip() not in {expected, f"codex-cli {expected}"}:
            raise RuntimeError(f"{binary} version does not match the template pin")
    return "codex 0.162.1; qwen-code 0.23.0"


if __name__ == "__main__":
    start(int(os.environ.get("ABX_SERVER_PORT", "9000")), policy=POLICY)
