#!/usr/bin/env python3
"""Local smoke for the codex template against E2E_BASE_URL.

Express runs go through scripts/express_e2e.py. This file does not create a
cloud sandbox. A model call is SKIP unless E2E_RUN_LLM=1 and a key is visible
in this process (the server process needs the same key).
"""
from __future__ import annotations

import os
import sys

import httpx

BASE_URL = os.environ.get("E2E_BASE_URL", "http://127.0.0.1:9000").rstrip("/")
WORK = os.environ.get("E2E_WORKSPACE") or os.environ.get("E2E_BASE_DIR") or "/tmp"
TIMEOUT = httpx.Timeout(connect=10.0, read=60.0, write=30.0, pool=10.0)
LLM_TIMEOUT = float(os.environ.get("E2E_LLM_TIMEOUT", "420"))
RUN_LLM = os.environ.get("E2E_RUN_LLM", "").strip().lower()
REQUIRE = os.environ.get("E2E_REQUIRE_LLM", "").strip().lower() in {"1", "true", "yes"}
MODEL = os.environ.get("E2E_MODEL", "").strip()
MARKER = "ABX_E2E_OK"
KEY_ENVS = ("OPENAI_API_KEY", "CODEX_API_KEY", "ABX_LLM_API_KEY")
COMMANDS = {
    "codex_version",
    "codex_setup_check",
    "codex_exec",
    "codex_config_write",
    "codex_agents_write",
    "codex",
}


def main() -> int:
    failures = 0
    home = os.path.join(WORK, "e2e_codex", "home")
    workspace = os.path.join(WORK, "e2e_codex", "workspace")
    os.makedirs(home, exist_ok=True)
    os.makedirs(workspace, exist_ok=True)

    def check(label: str, ok: bool, detail: str = "") -> None:
        nonlocal failures
        print(f"[{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""), flush=True)
        failures += not ok

    with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
        health = client.get("/health")
        check("GET /health", health.status_code == 200 and health.json().get("status") == "ok")

        listed = client.get("/commands")
        body = listed.json()
        entries = {item.get("name"): item for item in body.get("commands", []) if isinstance(item, dict)}
        check("GET /commands", listed.status_code == 200 and COMMANDS <= set(entries), str(sorted(entries)))

        exec_args = {item.get("name"): item.get("type") for item in entries.get("codex_exec", {}).get("args", [])}
        check(
            "codex_exec arg types",
            exec_args.get("prompt") == "string"
            and exec_args.get("json_events") == "boolean"
            and exec_args.get("timeout_s") == "integer"
            and exec_args.get("resume_all") == "boolean"
            and exec_args.get("sandbox") == "string",
            str(sorted(exec_args)),
        )

        unknown = client.post("/commands/__no_such_command__", json={})
        check("unknown command", unknown.status_code == 404 and unknown.json().get("type") == "ValueError")

        missing = client.post("/commands/codex_exec", json={})
        check(
            "codex_exec missing prompt",
            missing.status_code == 400 and "Required argument" in str(missing.json().get("error", "")),
            str(missing.status_code),
        )

        bad_sandbox = client.post(
            "/commands/codex_exec",
            json={"prompt": "do not run", "sandbox": "nope", "cwd": workspace},
        )
        bad_body = bad_sandbox.json()
        check(
            "codex_exec rejects sandbox",
            bad_sandbox.status_code == 500 and bad_body.get("type") == "ValueError",
            str(bad_body.get("error", ""))[:160],
        )

        setup = client.post("/commands/codex_setup_check", json={})
        setup_body = setup.json()
        result = setup_body.get("result") if isinstance(setup_body.get("result"), dict) else {}
        check(
            "codex_setup_check",
            setup.status_code == 200
            and result.get("bypass_flag") == "--dangerously-bypass-approvals-and-sandbox"
            and result.get("full_auto_supported") is False
            and isinstance(result.get("linux_sandbox"), bool)
            and isinstance(result.get("use_bypass"), bool)
            and result.get("pinned_version") == "0.162.1",
            f"linux_sandbox={result.get('linux_sandbox')} binary={result.get('binary_present')}",
        )
        if result.get("binary_present"):
            check(
                "bypass follows the probe",
                result.get("use_bypass") is (not result.get("linux_sandbox")),
            )
            version = client.post("/commands/codex_version", json={})
            version_body = version.json()
            check(
                "codex_version",
                version.status_code == 200 and version_body.get("result") == result.get("version"),
                str(version_body.get("result")),
            )
        else:
            version = client.post("/commands/codex_version", json={})
            check(
                "codex_version without binary",
                version.status_code == 500 and "not on PATH" in str(version.json().get("error", "")),
            )

        config = client.post(
            "/commands/codex_config_write",
            json={
                "base_url": "https://example.invalid/v1",
                "provider": "compatible",
                "env_key": "ABX_LLM_API_KEY",
                "model": "qwen-plus",
                "codex_home": home,
            },
        )
        config_body = config.json().get("result") if config.status_code == 200 else {}
        toml = config_body.get("toml", "") if isinstance(config_body, dict) else ""
        check(
            "codex_config_write",
            config.status_code == 200
            and config_body.get("wire_api") == "responses"
            and config_body.get("supports_websockets") is False
            and 'wire_api = "responses"' in toml
            and "supports_websockets = false" in toml
            and "ABX_LLM_API_KEY" in toml
            and "sk-" not in toml
            and os.path.isfile(os.path.join(home, "config.toml")),
            str(config.status_code),
        )

        chat = client.post(
            "/commands/codex_config_write",
            json={"base_url": "https://example.invalid/v1", "wire_api": "chat", "codex_home": home},
        )
        check(
            "wire_api chat rejected",
            chat.status_code == 500 and chat.json().get("type") == "ValueError",
            str(chat.json().get("error", ""))[:160],
        )

        reserved = client.post(
            "/commands/codex_config_write",
            json={"base_url": "https://example.invalid/v1", "provider": "openai", "codex_home": home},
        )
        check(
            "reserved provider rejected",
            reserved.status_code == 500 and reserved.json().get("type") == "ValueError",
        )

        agents = client.post(
            "/commands/codex_agents_write",
            json={"content": "Reply with the marker when asked.\n", "cwd": workspace},
        )
        agents_body = agents.json().get("result") if agents.status_code == 200 else {}
        path = agents_body.get("path", "") if isinstance(agents_body, dict) else ""
        check(
            "codex_agents_write",
            agents.status_code == 200 and path.endswith("/AGENTS.md") and os.path.isfile(path),
            path,
        )

        _llm(client, check)

    return 1 if failures else 0


def _llm(client: httpx.Client, check) -> None:
    test = "codex_exec model marker"
    forced_off = RUN_LLM in {"0", "false", "no"}
    has_key = any(os.environ.get(name, "").strip() for name in KEY_ENVS)
    if REQUIRE and forced_off:
        check(test, False, "E2E_REQUIRE_LLM=1 conflicts with E2E_RUN_LLM=0")
        return
    if forced_off or not has_key:
        print(f"[SKIP] {test}", flush=True)
        if REQUIRE or RUN_LLM in {"1", "true", "yes"}:
            check(test, False, "model key or E2E_RUN_LLM is missing")
        return
    payload: dict = {
        "prompt": f"Reply with exactly: {MARKER}",
        "sandbox": "bypass",
        "json_events": True,
        "ephemeral": True,
        "timeout_s": int(LLM_TIMEOUT),
    }
    if MODEL:
        payload["model"] = MODEL
    response = client.post("/commands/codex_exec", json=payload, timeout=LLM_TIMEOUT)
    body = response.json()
    result = body.get("result") if isinstance(body.get("result"), dict) else {}
    found = MARKER in str(result.get("last_message", "")) or MARKER in str(result.get("events", ""))
    check(
        test,
        response.status_code == 200 and found,
        f"HTTP {response.status_code} marker={found} error={str(body.get('error', ''))[:180]}",
    )


if __name__ == "__main__":
    sys.exit(main())
