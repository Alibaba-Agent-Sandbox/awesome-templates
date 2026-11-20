#!/usr/bin/env python3
"""Generate standalone Harness recipes from the maintained Codex recipe.

No generated project depends on a sibling directory at deployment time.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = "agents-api-codex"
SHARED_FILES = (
    ".dockerignore", ".gitignore", "commands.py", "e2e_test.py", "test_smoke.py",
    "server/bootstrap.py", "server/Dockerfile", "scripts/release.py",
    "scripts/smoke.py", "scripts/requirements.txt", "fixtures/csv-analysis/sales.csv",
    "fixtures/csv-analysis/aggregate.py", "fixtures/csv-analysis/tests/test_aggregate.py",
)
PROFILES = {
    "codex": dict(label="Codex", package="@openai/codex", version="0.162.1", binary="codex", keyEnv="OPENAI_API_KEY", baseUrlEnv="OPENAI_BASE_URL", modelEnv="OPENAI_MODEL", protocol="Responses", upstream="https://developers.openai.com/codex/noninteractive", license="Apache-2.0"),
    "qwen-code": dict(label="Qwen Code", package="@qwen-code/qwen-code", version="0.28.0", binary="qwen", keyEnv="OPENAI_API_KEY", baseUrlEnv="OPENAI_BASE_URL", modelEnv="OPENAI_MODEL", protocol="Chat Completions", upstream="https://qwenlm.github.io/qwen-code-docs/en/users/features/headless/", license="Apache-2.0"),
    "claude-code": dict(label="Claude Code", package="@anthropic-ai/claude-code", version="2.1.290", binary="claude", keyEnv="ANTHROPIC_API_KEY", baseUrlEnv="ANTHROPIC_BASE_URL", modelEnv="ANTHROPIC_MODEL", protocol="Anthropic Messages", upstream="https://code.claude.com/docs/en/headless", license="Proprietary"),
    "qoder": dict(label="Qoder", package="@qoder-ai/qodercli", version="1.1.90", binary="qoder", keyEnv="QODER_PERSONAL_ACCESS_TOKEN", baseUrlEnv=None, modelEnv="QODER_MODEL", protocol="Qoder service / PAT", upstream="https://docs.qoder.com/cli/run-in-scripts", license="Proprietary"),
    "opencode": dict(label="OpenCode", package="opencode-ai", version="1.19.5", binary="opencode", keyEnv="OPENAI_API_KEY", baseUrlEnv="OPENAI_BASE_URL", modelEnv="OPENAI_MODEL", protocol="OpenAI-compatible provider (v1 CLI)", upstream="https://opencode.ai/docs/cli/", license="MIT"),
    "deepseek-harness": dict(label="DeepSeek Harness", package="@deepseek-ai/dsh", version="0.2.2-rc.1", binary="dsh", keyEnv="DEEPSEEK_API_KEY", baseUrlEnv="DEEPSEEK_BASE_URL", modelEnv="DEEPSEEK_MODEL", protocol="Anthropic Messages", upstream="https://github.com/deepseek-ai/deepseek-harness", license="MIT"),
}


def profile(adapter: str) -> dict:
    return {"adapter": adapter, **PROFILES[adapter]}


def expected_files(adapter: str) -> dict[str, bytes]:
    """Return complete source bytes, varying only documented Harness inputs."""
    canonical = ROOT / CANONICAL
    name = "agents-api-" + adapter
    p = profile(adapter)
    files = {}
    for relative in SHARED_FILES:
        files[relative] = (canonical / relative).read_bytes()
    manifest = yaml.safe_load((canonical / "template.yaml").read_text())
    manifest["name"] = name
    manifest["vars"]["applicationName"] = name
    manifest["vars"]["adapter"] = adapter
    model = "${env('" + p["modelEnv"] + ("', 'auto')}" if adapter == "qoder" else "')}")
    for role in ("worker", "dispatcher", "gateway"):
        env = manifest["serving"][role]["props"]["environmentVariables"]
        env["AGENTS_MODEL"] = model
        for key in {entry["keyEnv"] for entry in PROFILES.values()} | {entry["baseUrlEnv"] for entry in PROFILES.values() if entry["baseUrlEnv"]}:
            env.pop(key, None)
        if role == "worker":
            env[p["keyEnv"]] = "${env('" + p["keyEnv"] + "')}"
            if p["baseUrlEnv"]:
                env[p["baseUrlEnv"]] = "${env('" + p["baseUrlEnv"] + "')}"
    files["template.yaml"] = yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True).encode()
    metadata = yaml.safe_load((canonical / "registry.yaml").read_text())
    metadata.update(name=name, version="0.2.0", tags=["agents-api", "gateway", "sessions", adapter])
    metadata["description"] = {"en": f"Run {p['label']} in session-owned sandboxes through one Gateway for tasks, files and results.", "zh": f"通过同一个 Gateway 调用 {p['label']}，在会话独占沙箱中执行任务、上传文件和下载结果。"}
    metadata["parameters"] = [entry for entry in metadata["parameters"] if entry["target"] != "/vars/adapter" and entry.get("environmentVariable") != "OPENAI_API_KEY"]
    metadata["parameters"].append(dict(target="/serving/worker/props/environmentVariables/" + p["keyEnv"], title={"en":p["label"] + " credential", "zh":p["label"] + " 凭据"}, environmentVariable=p["keyEnv"], sensitive=True))
    files["registry.yaml"] = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True).encode()
    files["server/harness.json"] = (json.dumps(p, indent=2, ensure_ascii=False) + "\n").encode()
    docker = (canonical / "Dockerfile").read_text()
    begin = docker.index("RUN npm install -g ")
    end = docker.index("\n\nRUN pip install", begin)
    docker = docker[:begin] + f"RUN npm install -g {p['package']}@{p['version']} \\\n    && {p['binary']} --version \\\n    && npm cache clean --force" + docker[end:]
    files["Dockerfile"] = docker.encode()
    for language in ("md", "zh-CN.md"):
        text = (canonical / ("README." + language)).read_text()
        text = text.replace(CANONICAL, name)
        text = text.replace("Codex 0.162.1", p["label"] + " " + p["version"])
        text = text.replace("run Codex,", "run " + p["label"] + ",").replace("运行 Codex、", "运行 " + p["label"] + "、")
        text = text.replace("`OPENAI_API_KEY`", "`" + p["keyEnv"] + "`").replace("`OPENAI_MODEL`", "`" + p["modelEnv"] + "`")
        text = text.replace("`OPENAI_BASE_URL`", "`" + (p["baseUrlEnv"] or "QODER_MODEL") + "`")
        text = text.replace("Responses API", p["protocol"])
        text = text.replace("through Responses.", "through " + p["protocol"] + ".")
        text = text.replace("支持 Responses API 的真实工具回合", "支持 " + p["protocol"] + " 的真实工具回合")
        text = text.replace("https://developers.openai.com/codex/noninteractive", p["upstream"])
        if adapter == "qoder":
            text = text.replace("The endpoint must use HTTPS.", "Qoder uses its native service and PAT; set QODER_MODEL to a model allowed by your account, or keep auto. No OpenAI endpoint is configured. BYOK requires the plan and account configuration documented by Qoder.")
            text = text.replace("端点必须使用 HTTPS。", "Qoder 使用原生服务与 PAT；QODER_MODEL 使用账号允许的模型，或保留 auto。无需填写 OpenAI 端点；BYOK 取决于官方方案和账号配置。")
            text = text.replace("`QODER_PERSONAL_ACCESS_TOKEN` / `QODER_MODEL` / `QODER_MODEL`", "`QODER_PERSONAL_ACCESS_TOKEN` / `QODER_MODEL`")
            text = text.replace("Obtain an authorized model credential and model ID from the selected service.", "Generate a PAT in your Qoder account and use an account-authorized model.")
            text = text.replace("The provider must support real tool rounds through Qoder service / PAT.", "Keep native Qoder authentication; no generic model endpoint is passed.")
            text = text.replace("从所选服务获取已授权凭据和模型 ID，写入私有 `.env`。", "从 Qoder 账号生成 PAT，并选择该账号允许的模型，写入私有 `.env`。")
            text = text.replace("提供商必须支持 Qoder service / PAT 的真实工具回合；", "保留 Qoder 原生认证；")
        if adapter == "opencode":
            if language == "md":
                text = text.replace("## Resources", "OpenCode v1 emits tool records after completion. This bridge cannot enforce a realtime per-tool deadline from those records; the whole-turn deadline and process cancellation still apply. Do not use maxToolSeconds as an isolation guarantee for this Harness.\n\n## Resources")
            else:
                text = text.replace("## 资源", "OpenCode v1 在工具完成后才输出工具记录，bridge 无法据此保证从真实开始时刻计时的单工具期限；整轮期限与进程取消仍适用。该 Harness 的 maxToolSeconds 不作为隔离保证。\n\n## 资源")
        files["README." + language] = text.encode()
    return files


def sync(check: bool = False) -> bool:
    differences = []
    for adapter in PROFILES:
        target = ROOT / ("agents-api-" + adapter)
        expected = expected_files(adapter)
        for relative, content in expected.items():
            file = target / relative
            if not file.is_file() or file.read_bytes() != content:
                differences.append(str(file.relative_to(ROOT)))
                if not check:
                    file.parent.mkdir(parents=True, exist_ok=True)
                    file.write_bytes(content)
        if check:
            for file in target.rglob("*"):
                relative = file.relative_to(target)
                if not file.is_file() or any(part.startswith(".") or part == "__pycache__" for part in relative.parts):
                    continue
                if relative.as_posix() not in expected and not (adapter == "codex" and relative.as_posix() == "scripts/test_release.py"):
                    differences.append(str(file.relative_to(ROOT)) + " (unexpected source)")
    for difference in differences:
        print(("DRIFT " if check else "WROTE ") + difference)
    return not (check and differences)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    raise SystemExit(0 if sync(parser.parse_args().check) else 1)
