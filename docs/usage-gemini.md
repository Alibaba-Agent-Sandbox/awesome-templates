# gemini

## 这是什么

`gemini` 是 Gemini CLI 的沙箱模板，状态是 experimental。镜像基于 `python:3.12-slim`，预装 Node.js 22 和 `@google/gemini-cli@0.64.0`。入口是 `python3 commands.py`，命名命令 `gemini` 执行：

```text
gemini -p <prompt> --yolo --model <model>
```

`<model>` 默认 `gemini-3.1-flash-lite`。超时 600 秒。`prompt` 必填。没有 `GEMINI_API_KEY` 时命令失败，不会启动 CLI。

## 本地 e2e

```bash
python3 -m pip install agent-sandbox-server httpx
python3 scripts/run_local_e2e.py
```

根目录这条命令强制 `E2E_RUN_LLM=0`，不转发密钥。模型调用是 SKIP，退出码 0 只说明 server 契约过了。

带密钥时，在 `gemini/` 里让服务和测试都能读到 `GEMINI_API_KEY`：

```bash
GEMINI_API_KEY=<你的密钥> E2E_REQUIRE_LLM=1 E2E_BASE_URL=http://127.0.0.1:9000 python3 e2e_test.py
```

输出必须包含 `ABX_E2E_OK`。缺密钥是 FAIL。

## 极速版

```bash
abx template install alibaba-agent-sandbox/awesome-templates//gemini
abx deploy
abx create --template gemini --env GEMINI_API_KEY=<你的密钥>
abx run <sandbox-id> gemini --json-args '{"prompt":"只回复 ABX_E2E_OK"}'
```

Python：

```python
await sandbox.run("gemini", prompt="只回复 ABX_E2E_OK", model="gemini-3.1-flash-lite")
```

这是极速版上发布后的具名命令。E2B 的具名命令是 E8004，不要在 E2B 上调用 `sandbox.run("gemini", ...)`。
