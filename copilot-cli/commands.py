"""Explicit BYOK native Copilot CLI, with isolated per-call state and fixed tools."""
from __future__ import annotations
import importlib.util
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import tempfile
from urllib.parse import urlsplit
from agent_sandbox.server import command, start

_CONFIG={key:os.environ.get(key, "") for key in ("COPILOT_PROVIDER_BASE_URL", "COPILOT_PROVIDER_API_KEY", "COPILOT_MODEL")}
_ROOT=Path(os.environ.get("WORKSPACE", "/home/user/app")).resolve()
_NATIVE="1.0.100"


def _env(private: Path, *, model: bool) -> dict[str,str]:
    env={k:os.environ[k] for k in ("PATH","SSL_CERT_FILE","SSL_CERT_DIR","NODE_EXTRA_CA_CERTS") if k in os.environ}
    env.update(HOME=str(private),COPILOT_HOME=str(private/"copilot"),XDG_CACHE_HOME=str(private/"cache"),
               XDG_CONFIG_HOME=str(private/"config"),XDG_STATE_HOME=str(private/"state"),
               TMPDIR=str(private),LANG="C.UTF-8",COPILOT_OFFLINE="true",COPILOT_AUTO_UPDATE="false",
               NO_COLOR="1",TERM="dumb")
    if model:
        base=_CONFIG["COPILOT_PROVIDER_BASE_URL"];key=_CONFIG["COPILOT_PROVIDER_API_KEY"];name=_CONFIG["COPILOT_MODEL"]
        if not base or len(base)>2048:raise ValueError("set COPILOT_PROVIDER_BASE_URL before starting this command server")
        try:u=urlsplit(base);port=u.port
        except ValueError:raise ValueError("invalid provider URL") from None
        if u.scheme!="https" and not (u.scheme=="http" and u.hostname in ("127.0.0.1","localhost","::1")):
            raise ValueError("provider URL requires HTTPS or literal local development HTTP")
        if not u.hostname or u.username or u.password or u.query or u.fragment or any(c.isspace() for c in base):raise ValueError("invalid provider URL")
        if not key or len(key)>8192 or any(c in key for c in "\r\n\x00"):raise ValueError("set a bounded COPILOT_PROVIDER_API_KEY before starting this command server")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}",name):raise ValueError("set a bounded COPILOT_MODEL before starting this command server")
        env.update(_CONFIG,COPILOT_PROVIDER_TYPE="openai",COPILOT_PROVIDER_WIRE_API="completions",
                   COPILOT_PROVIDER_TRANSPORT="http",COPILOT_PROVIDER_MAX_PROMPT_TOKENS="65536",
                   COPILOT_PROVIDER_MAX_OUTPUT_TOKENS="4096")
    return env


def _run(args: list[str], *, cwd: Path, timeout: int, model: bool) -> dict:
    executable=shutil.which("copilot")
    if not executable:raise RuntimeError("pinned Copilot CLI is not installed")
    spec=importlib.util.spec_from_file_location("owned_copilot_process_"+secrets.token_hex(8),Path(__file__).with_name("process.py"))
    worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
    with tempfile.TemporaryDirectory(prefix="abx-copilot-home-") as value:
        private=Path(value);private.chmod(0o700)
        env=_env(private,model=model)
        code,out,err=worker.run([executable,*args],cwd=str(cwd),timeout=timeout,env=env)
    # Preserve native nonzero status; never turn native failure into a successful string.
    for key in [_CONFIG["COPILOT_PROVIDER_API_KEY"]]:
        if key:
            for text in {key,json.dumps(key,ensure_ascii=True)[1:-1],json.dumps(key,ensure_ascii=False)[1:-1]}:
                out=out.replace(text,"[REDACTED]");err=err.replace(text,"[REDACTED]")
    return {"stdout":out,"stderr":err,"exit_code":code,"native_version":_NATIVE}


@command("copilot_version",description="Read the installed pinned native version without model or GitHub credentials.")
def copilot_version() -> dict:
    result=_run(["--version","--no-auto-update","--disable-client-telemetry"],cwd=_ROOT,timeout=30,model=False)
    if result["exit_code"]!=0 or not re.search(r"GitHub Copilot CLI 1\.0\.100\.",result["stdout"]):
        raise RuntimeError("installed native Copilot CLI version does not match1.0.100")
    return {"native_version":_NATIVE}


@command("copilot_setup_check",description="Read configuration presence only; no network, secret values or login.")
def copilot_setup_check() -> dict:
    return {"mode":"openai-compatible-byok","base_url_set":bool(_CONFIG["COPILOT_PROVIDER_BASE_URL"]),
            "api_key_set":bool(_CONFIG["COPILOT_PROVIDER_API_KEY"]),"model_set":bool(_CONFIG["COPILOT_MODEL"]),
            "github_auth_required":False}


@command("copilot",description="Run a bounded native BYOK prompt; file changes require allow_write=true.")
def copilot(prompt: str, cwd: str="", allow_write: bool=False, command_timeout: int=300) -> dict:
    if not isinstance(prompt,str) or not prompt.strip() or len(prompt.encode())>32768 or "\x00" in prompt:
        raise ValueError("prompt must contain1..32768UTF-8 bytes without NUL")
    if not isinstance(cwd,str) or len(cwd.encode())>4096 or "\x00" in cwd:raise ValueError("invalid cwd")
    if type(allow_write) is not bool:raise ValueError("allow_write must be boolean")
    if type(command_timeout) is not int or not 1<=command_timeout<=600:raise ValueError("command_timeout must be1..600seconds")
    directory=(_ROOT/cwd).resolve()
    if not directory.is_relative_to(_ROOT) or not directory.is_dir():raise ValueError("cwd must be an existing directory inside WORKSPACE")
    tools=["view","glob","grep"]+(["edit","create","apply_patch"] if allow_write else [])
    args=["--no-auto-update","--disable-client-telemetry","--no-custom-instructions","--no-ask-user",
          "--no-experimental","--no-bash-env","--no-remote","--no-remote-export","--disable-builtin-mcps",
          "--disallow-temp-dir","--allow-all-tools","--stream=off","--output-format=json","--log-level=none",
          "--secret-env-vars=COPILOT_PROVIDER_API_KEY","--available-tools",*tools,"--prompt="+prompt]
    return _run(args,cwd=directory,timeout=command_timeout,model=True)


if __name__=="__main__":
    start(int(os.environ.get("ABX_SERVER_PORT","9000")))
