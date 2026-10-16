# codex

`codex` 是 OpenAI Codex CLI 的沙箱模板。镜像基于 `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`，钉 `@openai/codex@0.162.1`。命名命令在 `agent-sandbox-server` 上，端口 9000。没有镜像 `CMD` / `ENTRYPOINT`。

## 命名命令

| 命令 | 作用 |
|---|---|
| `codex_version` | `codex --version`，返回 `X.Y.Z` |
| `codex_setup_check` | 探测 Linux 沙箱。失败时 `bypass_flag` 为 `--dangerously-bypass-approvals-and-sandbox` |
| `codex_exec` | `codex exec --json`。参数包括 `prompt`、`model`、`cwd`、`sandbox`、`approval`、`resume` |
| `codex_config_write` | 写 `$CODEX_HOME/config.toml`。`wire_api` 只能是 `responses` |
| `codex_agents_write` | 把 `AGENTS.md` 写到工作目录 |
| `codex` | `codex_exec` 的兼容别名，只有 `prompt` 和 `model` |

0.162.1 不接受旧的 `codex -p ... --output-format json`，也不接受 `--full-auto`。沙箱探测失败时（Express 上常见：没有 capabilities，bubblewrap user namespace / seccomp / 遗留 landlock 起不来），仅 `sandbox=auto` 自动加上 `--dangerously-bypass-approvals-and-sandbox`；显式 `sandbox=bypass` 也使用该标志。显式 `read-only`、`workspace-write` 或 `danger-full-access` 在探测失败时会在创建工作目录、git 或配置之前拒绝执行。探测成功且 `sandbox=auto` 时用 `--sandbox workspace-write` 和 `approval_policy="never"`。

`apply-patch`（issue #60）是独立的 `codex-apply-patch` 文件工具，不在这个目录里构建。`codex-agent-api`（issue #23）是 Agents API HTTP 服务，和这里的 CLI 命令不是同一个控制面。

## 本地 e2e

仓库根目录，已安装 `agent-sandbox-server`、`httpx`、`pyyaml`：

```bash
python3 scripts/check_template.py codex
python3 scripts/run_local_e2e.py
```

只跑本目录时：

```bash
cd codex
ABX_SERVER_PORT=9000 python3 commands.py
```

```bash
cd codex
E2E_BASE_URL=http://127.0.0.1:9000 python3 e2e_test.py
```

根目录脚本强制 `E2E_RUN_LLM=0`，并且不把密钥传给子进程。这不算模型验收。带密钥时：

```bash
E2E_BASE_URL=http://127.0.0.1:9000 E2E_RUN_LLM=1 E2E_REQUIRE_LLM=1 E2E_MODEL=qwen-plus python3 e2e_test.py
```

提示词是 `Reply with exactly: ABX_E2E_OK`。跑测试的进程和 `commands.py` 进程都要看得到密钥。

## 极速版

```bash
abx template deploy ./codex -y --generation 2
abx create --template <template-id> -y --env OPENAI_API_KEY=<密钥> --env OPENAI_BASE_URL=<兼容端点> --env CODEX_MODEL=qwen-plus
abx run <sandbox-id> codex_exec --json-args '{"prompt":"总结工作区","model":"qwen-plus"}'
```

```python
await sandbox.run("codex_exec", prompt="总结工作区", model="qwen-plus")
```

`abx exec` 和 `sandbox.commands.run` 是 shell，不会自动加上 `codex exec` 的参数。

## 环境变量

| 变量 | 作用 |
|---|---|
| `OPENAI_API_KEY` / `CODEX_API_KEY` / `ABX_LLM_API_KEY` | 密钥。`config.toml` 只写变量名（`env_key`）。 |
| `OPENAI_BASE_URL` / `ABX_LLM_BASE_URL` | OpenAI 兼容基址，例如 DashScope `/compatible-mode/v1`。 |
| `CODEX_MODEL` | 可选模型名。 |
| `CODEX_HOME` | 默认 `/home/user/.codex`。 |
| `WORKSPACE` | 默认 `/home/user/workspace`。 |
| `E2E_RUN_LLM` | `0` 跳过模型调用；`1` 强制调用。 |
