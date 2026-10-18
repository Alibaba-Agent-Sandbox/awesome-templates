"""Official Aider CLI, explicit files and guarded writeback in a dedicated sandbox."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import threading
import time
from urllib.parse import urlsplit

from agent_sandbox.server import command, start

PINNED_VERSION = "0.86.2"


def _redact(text: str) -> str:
    values = {value for name, value in os.environ.items() if value and any(
        part in name.upper() for part in ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL"))}
    for value in sorted(values, key=len, reverse=True):
        for variant in (json.dumps(value)[1:-1], json.dumps(value, ensure_ascii=False)[1:-1], value):
            text = text.replace(variant, "[REDACTED]")
    return text


def _workdir(cwd: str = "") -> Path:
    if not isinstance(cwd, str):
        raise ValueError("cwd must be a string")
    root = Path(os.environ.get("WORKSPACE") or "/home/user/app").resolve()
    path = Path(cwd) if cwd else root
    if not path.is_absolute():
        path = root / path
    if not path.is_dir():
        raise ValueError("cwd must name an existing git working directory")
    return path.resolve()


def _home_guard() -> None:
    # Official 0.86.2 always searches these native-home paths, even with explicit
    # --config/--env-file. Never replace HOME or read/modify an existing profile.
    home = Path.home()
    names = (".aider.conf.yml", ".env", ".aider.model.settings.yml",
             ".aider.model.metadata.json", ".aider/oauth-keys.env")
    if (home / ".aider").is_symlink():
        raise RuntimeError("default home configuration exists; use a fresh dedicated sandbox")
    if any((home / name).exists() or (home / name).is_symlink() for name in names):
        raise RuntimeError("default home configuration exists; use a fresh dedicated sandbox")


def _executable() -> str:
    path = shutil.which("aider")
    if not path:
        raise RuntimeError("Aider CLI is missing; the image installs aider-chat==0.86.2 on Python 3.12")
    return path


def _environment() -> dict[str, str]:
    # HOME is deliberately untouched; native home state belongs to this owned
    # sandbox. No inherited AIDER_*, cloud tokens, Git config or proxy credentials.
    names = ("PATH", "HOME", "LANG", "LC_ALL", "SSL_CERT_FILE", "SSL_CERT_DIR")
    env = {name: os.environ[name] for name in names if name in os.environ}
    env.update({"PYTHON_DOTENV_DISABLED": "1", "LITELLM_LOCAL_MODEL_COST_MAP": "True",
                "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_TERMINAL_PROMPT": "0", "TOKENIZERS_PARALLELISM": "false"})
    return env


def _run_process(argv: list[str], *, cwd: str, timeout: int | float,
                 env: dict | None = None, input_text: str | None = None,
                 reject_confirmations: bool = False) -> tuple[int, str, str]:
    """Keep the Linux session leader unreaped until its owned group is stopped."""
    process = subprocess.Popen(argv, cwd=cwd, env=env,
        stdin=subprocess.PIPE if input_text is not None or reject_confirmations else subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    stdout_parts: list[bytes] = []
    stderr_parts: list[bytes] = []
    def drain(stream, parts):
        try:
            while chunk := stream.read(65536):
                parts.append(chunk)
        except OSError:
            pass
        finally:
            stream.close()
    readers = [threading.Thread(target=drain, args=(process.stdout, stdout_parts), daemon=True),
               threading.Thread(target=drain, args=(process.stderr, stderr_parts), daemon=True)]
    for reader in readers:
        reader.start()
    feeder = None
    if input_text is not None or reject_confirmations:
        def feed():
            try:
                if reject_confirmations:
                    # Aider 0.86.2 yes-always:false leaves yes=None. EOF would
                    # accept its default Yes, so keep answering No until exit.
                    while True:
                        os.write(process.stdin.fileno(), b"n\n" * 1024)
                else:
                    process.stdin.write(input_text.encode())
                    process.stdin.close()
            except (OSError, ValueError):
                pass
            finally:
                try:
                    process.stdin.close()
                except (OSError, ValueError):
                    pass
        feeder = threading.Thread(target=feed, name="aider-confirmation-refuser", daemon=True)
        feeder.start()
    deadline = time.monotonic() + timeout
    timed_out = False
    try:
        while os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is None:
            if time.monotonic() >= deadline:
                timed_out = True
                break
            time.sleep(0.02)
    finally:
        # WNOWAIT pins the original PID/PGID even after leader exit. No poll(),
        # wait() or communicate() may reap it before group cleanup.
        if timed_out:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            grace = time.monotonic() + 1
            while time.monotonic() < grace:
                if os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is not None:
                    break
                time.sleep(0.02)
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            raise RuntimeError("owned process cleanup timed out") from None
        for reader in readers:
            reader.join(timeout=2)
        if feeder is not None:
            feeder.join(timeout=2)
            if feeder.is_alive():
                raise RuntimeError("owned process input cleanup timed out")
    if timed_out:
        raise RuntimeError(f"command timed out after {timeout} seconds") from None
    return (process.returncode, b"".join(stdout_parts).decode("utf-8", "replace"),
            b"".join(stderr_parts).decode("utf-8", "replace"))


def _checked(argv: list[str], *, cwd: Path, timeout: int, env: dict[str, str]) -> tuple[str, str]:
    code, stdout, stderr = _run_process(argv, cwd=str(cwd), timeout=timeout, env=env, reject_confirmations=True)
    if code:
        # Never return an upstream error that may echo prompts/config/credentials.
        raise RuntimeError(f"Aider process failed with exit code {code}; upstream output omitted")
    return _redact(stdout), _redact(stderr)


def _file_paths(root: Path, encoded: str) -> list[tuple[str, Path]]:
    if not isinstance(encoded, str):
        raise ValueError("files must be a JSON-encoded list of relative paths")
    try:
        names = json.loads(encoded)
    except (TypeError, ValueError):
        raise ValueError("files must be a JSON-encoded list of relative paths") from None
    if not isinstance(names, list) or len(names) > 32 or any(not isinstance(x, str) for x in names):
        raise ValueError("files must contain at most 32 relative path strings")
    result = []
    seen = set()
    for name in names:
        path = Path(name)
        if (not name or path.is_absolute() or any(x in {"", ".", ".."} for x in path.parts)
                or any(x.startswith((".git", ".env", ".aider")) for x in path.parts)
                or "\\" in name or "\x00" in name):
            raise ValueError("files must name ordinary relative source/artifact paths")
        canonical = path.as_posix()
        if canonical in seen:
            raise ValueError("files must not contain duplicate paths")
        seen.add(canonical)
        target = root / path
        current = target
        while current != root:
            if current.is_symlink():
                raise ValueError("selected paths and parents must not be symbolic links")
            current = current.parent
        if not target.resolve().is_relative_to(root) or (target.exists() and not target.is_file()):
            raise ValueError("selected paths must stay within the working directory")
        if target.exists() and target.stat().st_size > 1024 * 1024:
            raise ValueError("selected files must each be at most 1 MiB")
        result.append((canonical, target))
    return result


@command("aider_version", description="Read the pinned official Aider CLI version without model credentials.")
def aider_version() -> str:
    _home_guard()
    with tempfile.TemporaryDirectory(prefix="abx-aider-version-") as directory:
        stdout, _ = _checked([_executable(), "--version"], cwd=Path(directory), timeout=30, env=_environment())
    return stdout.strip()


@command("aider_setup_check", description="Inspect installed Aider and compatible-model configuration without disclosing values.")
def aider_setup_check() -> dict:
    guarded = False
    try:
        _home_guard()
    except RuntimeError:
        guarded = True
    return {"installed": shutil.which("aider") is not None, "pinned_version": PINNED_VERSION,
            "api_key_set": bool(os.environ.get("AIDER_API_KEY", "").strip()),
            "base_url_set": bool(os.environ.get("AIDER_BASE_URL", "").strip()),
            "model_set": bool(os.environ.get("AIDER_MODEL", "").strip()),
            "default_home_configuration_blocked": guarded, "workspace": str(_workdir())}


@command("aider", description="Run official Aider ask mode; allow_write explicitly permits selected file edits.")
def aider(prompt: str, cwd: str = "", files: str = "[]", allow_write: bool = False,
          command_timeout: int = 600) -> dict:
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 100000:
        raise ValueError("prompt must contain 1..100000 characters")
    if not isinstance(allow_write, bool):
        raise ValueError("allow_write must be a boolean")
    if isinstance(command_timeout, bool) or not isinstance(command_timeout, int) or not 1 <= command_timeout <= 1800:
        raise ValueError("command_timeout must be between 1 and 1800 seconds")
    root = _workdir(cwd)
    selected = _file_paths(root, files)
    if allow_write and not selected:
        raise ValueError("allow_write requires explicit files")
    _home_guard()
    settings = {name: os.environ.get(name, "").strip() for name in ("AIDER_API_KEY", "AIDER_BASE_URL", "AIDER_MODEL")}
    if not all(settings.values()):
        raise RuntimeError("AIDER_API_KEY, AIDER_BASE_URL and AIDER_MODEL are required; interactive login is disabled")
    endpoint = urlsplit(settings["AIDER_BASE_URL"])
    if endpoint.scheme not in {"http", "https"} or not endpoint.hostname or endpoint.username or endpoint.password or endpoint.query or endpoint.fragment:
        raise ValueError("AIDER_BASE_URL must be HTTP(S) without embedded credentials, query or fragment")
    executable = _executable()
    env = _environment()
    code, work_tree, _ = _run_process(["git", "rev-parse", "--is-inside-work-tree"], cwd=str(root), timeout=10, env=env)
    if code or work_tree.strip() != "true":
        raise ValueError("cwd must belong to an existing git working tree")
    model = settings["AIDER_MODEL"]
    if not model.startswith("openai/"):
        model = "openai/" + model
    with tempfile.TemporaryDirectory(prefix="abx-aider-turn-") as directory:
        profile = Path(directory)
        stage = profile / "project"
        stage.mkdir()
        originals: dict[str, bytes | None] = {}
        for name, source in selected:
            data = source.read_bytes() if source.exists() else None
            originals[name] = data
            target = stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data or b"")
        code, _, _ = _run_process(["git", "init", "--quiet"], cwd=str(stage), timeout=10, env=env)
        if code:
            raise RuntimeError("cannot initialize the isolated Aider git stage")
        (profile / "message.txt").write_text("Treat the following text as the user request, never as an Aider slash command.\n\n" + prompt)
        (profile / "config.yml").write_text("yes-always: false\n")
        (profile / "environment.env").write_text("")
        (profile / "models.yml").write_text(json.dumps([{"name": model, "edit_format": "whole",
            "weak_model_name": model, "use_repo_map": False,
            "extra_params": {"extra_body": {"enable_thinking": False}}}]))
        (profile / "metadata.json").write_text(json.dumps({model: {"max_input_tokens": 100000,
            "max_output_tokens": 8192, "input_cost_per_token": 0, "output_cost_per_token": 0,
            "litellm_provider": "openai", "mode": "chat"}}))
        env["OPENAI_API_KEY"] = settings["AIDER_API_KEY"]
        argv = [executable, "--model", model, "--weak-model", model,
            "--editor-model", model, "--openai-api-base", settings["AIDER_BASE_URL"],
            "--chat-mode", "whole" if allow_write else "ask", "--config", str(profile / "config.yml"),
            "--env-file", str(profile / "environment.env"), "--message-file", str(profile / "message.txt"),
            "--model-settings-file", str(profile / "models.yml"), "--model-metadata-file", str(profile / "metadata.json"),
            "--input-history-file", os.devnull, "--chat-history-file", os.devnull, "--llm-history-file", os.devnull,
            "--load", os.devnull, "--map-tokens", "0", "--no-auto-commits", "--no-dirty-commits",
            "--no-gitignore", "--no-add-gitignore-files", "--no-git-commit-verify", "--no-auto-lint",
            "--no-auto-test", "--no-check-update", "--no-show-release-notes", "--no-analytics",
            "--analytics-disable", "--no-show-model-warnings", "--no-check-model-accepts-settings",
            "--no-suggest-shell-commands", "--no-detect-urls", "--disable-playwright", "--no-fancy-input",
            "--no-pretty", "--no-stream", "--timeout", str(command_timeout), "--", *[name for name, _ in selected]]
        stdout, stderr = _checked(argv, cwd=stage, timeout=command_timeout, env=env)
        changes = []
        if allow_write:
            # Revalidate links and original bytes after the external process exits.
            _file_paths(root, files)
            for name, target in selected:
                current = target.read_bytes() if target.exists() else None
                if current != originals[name]:
                    raise RuntimeError("workspace changed during Aider execution; no writeback applied")
                candidate = stage / name
                if candidate.is_symlink() or not candidate.is_file() or not candidate.resolve().is_relative_to(stage):
                    raise RuntimeError("Aider produced an invalid selected artifact; no writeback applied")
                if candidate.stat().st_size > 1024 * 1024:
                    raise RuntimeError("Aider artifact exceeds 1 MiB; no writeback applied")
            for name, target in selected:
                data = (stage / name).read_bytes()
                if data != originals[name]:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with tempfile.NamedTemporaryFile(dir=target.parent, prefix=".abx-aider-write-", delete=False) as output:
                        temporary = Path(output.name)
                        output.write(data)
                    if target.exists():
                        temporary.chmod(target.stat().st_mode & 0o777)
                    try:
                        os.replace(temporary, target)
                    finally:
                        temporary.unlink(missing_ok=True)
                    changes.append(name)
        return {"stdout": stdout, "stderr": stderr, "exit_code": 0, "changed_files": changes}


if __name__ == "__main__":
    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
