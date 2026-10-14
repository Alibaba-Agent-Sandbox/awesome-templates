# gemini 镜像构建记录（2026-10-14）

`docker build -t abx-gemini:local gemini/` 退出码 0。镜像 id `979bcdd2f13b`。

构建日志里的固定版本行是：

```text
npm install -g @google/gemini-cli@0.64.0
gemini --version
0.64.0
```

同一层还安装了构建上下文里的 `agent-sandbox-server` wheel（0.3.0）。这个包还没有发到 PyPI，所以这次构建用的是本地 wheel，和 `abx template deploy` 把 wheel 放进构建上下文的方式相同。没有 wheel 时 Dockerfile 会改走 `pip install agent-sandbox-server`。

这次没有 `GEMINI_API_KEY`，没有跑带标记 `ABX_E2E_OK` 的模型调用。`gemini` 仍是 `experimental`。
