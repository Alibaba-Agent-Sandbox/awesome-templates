# Verify command source on an existing Express base

This diagnostic checks changed command source against real Express filesystem,
process, HTTP and optional model services. It does not build a template Dockerfile,
deploy a template image, or qualify a provider in `tested_on`.

Use a paired client/server source checkout. Build the server wheel from the exact
SDK commit under test, install the client locally, and supply authorized cloud
configuration through the caller's environment. The diagnostic never reads `.env`
itself. Do not put credentials in command arguments, evidence, or shell tracing.

```bash
python -m build --wheel --outdir /tmp/server-wheel ../python-sdk/server-sdk
python scripts/express_runtime_e2e.py python-hello \
  --server-wheel /tmp/server-wheel/agent_sandbox_server-0.3.0-py3-none-any.whl \
  --output-dir /tmp/python-hello-runtime \
  --sdk-source-commit SDK_COMMIT
```

The runner also accepts `node-web`, `browser-automation` and `opencode`.
Node web uploads its public sample and a dependency-free package fixture; browser
automation installs Playwright 1.58.0 and Chromium, using only system libraries
already in the base. It never invokes sudo or installs system dependencies; a
missing library or failed browser launch is a failed run, not an isolation fallback.
OpenCode requires `ABX_LLM_API_KEY`, `ABX_LLM_BASE_URL` in the caller environment
and `--model dashscope/<model>`. It uses the checked-in public config and pinned
1.19.0 CLI; credentials are supplied only to the remote process environment.

For `codex` and `codex-agent-api`, supply `OPENAI_API_KEY` and `OPENAI_BASE_URL`
through the environment, select a Responses-compatible model with `--model`, and
replace `python-hello` above with the chosen template name. Model acceptance is
required, so a skipped model task cannot produce a passing report. The Codex API
case starts the production `agent-sandbox-server serve --commands` loader, rather
than substituting the command file's direct entry point.

The runner creates one uniquely tagged base sandbox, uploads only its command
source and the selected wheel, installs the pinned upstream dependency, starts
an authenticated server, and runs the external HTTP verifier. Model tests verify
actual coding work and controller-owned assertions. The verifier subprocess gets
only its required runtime/proxy environment and server token. The runner attempts
to kill its owned sandbox in `finally`, including when installation, startup or
verification fails; a failed cleanup is itself a failed check.

The JSON report records source and wheel SHA-256, client version, caller-supplied
SDK commit, every check and cleanup result. Inspect the sanitized installation and
HTTP logs as well as the exit code. A caller-supplied commit label is provenance,
not proof that the wheel was built from a clean tree; reviewers should reproduce
the build and compare the wheel hash. A platform denial is a failure: stop that
path and record its original reason rather than changing network or permissions.

Successful recorded checks are source-runtime evidence; failed runs remain failures even when cleanup succeeds.
Docker image build (L1), deployment of that image (L2), other providers and full
candidate acceptance remain separate work. See the individual template READMEs
and evidence; the catalog's provider acceptance stays empty until its gates pass.

## 中文

该诊断在已有 Express base 中验证改动后的命令源码，覆盖真实文件、进程、HTTP，
以及可选的模型任务。它不构建 Dockerfile，不部署模板镜像，也不能据此填写
`tested_on`。按上方命令构建指定 SDK 提交的 server wheel，安装配套 client，
由调用方通过已有授权环境提供配置；脚本本身不读取 `.env`，不要把凭据写进参数
或日志。

`codex` 与 `codex-agent-api` 需环境中的模型配置和 `--model`；模型任务强制执行，
跳过不能算通过。API 模板使用正式 `serve --commands` 启动入口。脚本仅上传命令
源码和 wheel，创建带唯一标签的自有实例，并在 `finally` 中尝试销毁；清理失败
也算验证失败。HTTP 子进程只获得运行所需的环境及 server token。

证据记录源码和 wheel 哈希、client 版本、调用方声明的 SDK 提交、各项检查及
资源清理结果；提交声明不代替干净源码构建证明，应复现构建并比对哈希。
遇到平台拒绝需保留原因，停止该路径，不更改网络或权限绕过。
源码运行验证与 Docker 构建、镜像部署、其他 provider 验收分别记录，不混称通过。
