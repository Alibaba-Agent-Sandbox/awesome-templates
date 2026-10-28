# Agent Sandbox 模板

**中文** | [English](README.md)

为 AI Agent 准备可复用的运行环境：浏览器自动化、编码工具、Web 服务、文档处理与基准任务。每个模板提供自己的配置、命令示例和资源清理说明。

[浏览模板](https://registry.agent-sandbox.cn/templates/) · [使用指南](docs/using-templates.zh-CN.md) · [提供方配置](docs/provider-preparation.zh-CN.md)

## 快速开始

先[安装 abx CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox#installation)（0.5.8 或更新版本），按[使用指南](docs/using-templates.zh-CN.md)准备所选提供方的凭据和构建环境，再启动无需模型的入门模板：

```bash
abx --provider alicloud-express template launch Alibaba-Agent-Sandbox/awesome-templates//python-hello
```

CLI 会引导补齐必要配置，自动生成并保存默认应用认证令牌，后续命令复用。使用模型的模板还需要其 README 指定的模型账号或 API 配置。

启动后，将 `<sandbox-id>` 替换为返回的沙箱 ID：

```bash
abx run <sandbox-id> hello --arg name=Ada
abx kill <sandbox-id>
```

预期输出为 `Hello, Ada!`。`kill` 删除运行中的沙箱；保留的镜像和模板按[清理说明](docs/using-templates.zh-CN.md#导出文件与清理)另行删除。

## 选择模板

源码模板需要构建。下方按任务分类，具体依赖、参数和支持范围见各模板说明；在 Registry 中可按平台查看启动方式。

### 入门与应用服务

| 模板 | 用途 |
| --- | --- |
| [python-hello](python-hello/README.zh-CN.md) | 提供 hello 命令的最小 Python 应用 |
| [node-web](node-web/README.zh-CN.md) | Node.js Web 服务 |
| [next-app](next-app/README.zh-CN.md) | Next.js、Vite 项目与预览服务 |
| [code-server](code-server/README.zh-CN.md) | 带认证的浏览器 IDE |
| [dev-services](dev-services/README.zh-CN.md) | PostgreSQL 与 Redis 服务 |
| [polyglot-toolchain](polyglot-toolchain/README.zh-CN.md) | Go、Rust 和 Java 编译环境 |

### 浏览器与桌面

| 模板 | 用途 |
| --- | --- |
| [browser-automation](browser-automation/README.zh-CN.md) | Playwright 与 Chromium 自动化 |
| [browser-use](browser-use/README.zh-CN.md) | 使用 browser-use 的模型驱动浏览器自动化 |
| [stagehand](stagehand/README.zh-CN.md) | Stagehand 浏览器操作与内容提取 |
| [chrome](chrome/README.zh-CN.md) | 带 CDP 和远程桌面的有界面 Chrome |
| [osworld](osworld/README.zh-CN.md) | OSWorld Linux 浏览器任务 |

### 编码 Agent

| 模板 | 用途 |
| --- | --- |
| [claude-code](claude-code/README.zh-CN.md) | Claude Code 编码 Agent |
| [copilot-cli](copilot-cli/README.zh-CN.md) | Copilot Cli 编码 Agent |
| [codex](codex/README.zh-CN.md) | Codex 编码 Agent |
| [qoder](qoder/README.zh-CN.md) | Qoder 编码 Agent |
| [qwen-code](qwen-code/README.zh-CN.md) | Qwen Code 编码 Agent |
| [deepagents](deepagents/README.zh-CN.md) | Deepagents 编码 Agent |
| [deepseek-harness](deepseek-harness/README.zh-CN.md) | Deepseek Harness 编码 Agent |
| [hermes-agent](hermes-agent/README.zh-CN.md) | Hermes Agent 编码 Agent |
| [openclaw](openclaw/README.zh-CN.md) | Openclaw 编码 Agent |
| [opencode](opencode/README.zh-CN.md) | Opencode 编码 Agent |
| [amp](amp/README.zh-CN.md) | Amp 编码 Agent |
| [droid](droid/README.zh-CN.md) | Droid 编码 Agent |
| [gemini](gemini/README.zh-CN.md) | Gemini 编码 Agent |
| [pi](pi/README.zh-CN.md) | Pi 编码 Agent |
| [aider](aider/README.zh-CN.md) | Aider 编码 Agent |
| [swe](swe/README.zh-CN.md) | Swe 编码 Agent |
| [kimi-code](kimi-code/README.zh-CN.md) | Kimi Code 编码 Agent |
| [goose](goose/README.zh-CN.md) | Goose 编码 Agent |
| [crush](crush/README.zh-CN.md) | Crush 编码 Agent |
| [grok](grok/README.zh-CN.md) | Grok 编码 Agent |
| [cline](cline/README.zh-CN.md) | Cline 编码 Agent |
| [prime-agent](prime-agent/README.zh-CN.md) | Prime Agent 编码 Agent |
| [muse](muse/README.zh-CN.md) | Muse 编码 Agent |
| [cursor-agent](cursor-agent/README.zh-CN.md) | Cursor Agent 编码 Agent |
| [devin](devin/README.zh-CN.md) | Devin 编码 Agent |

### Agent API 与工具

| 模板 | 用途 |
| --- | --- |
| [codex-agent-api](codex-agent-api/README.zh-CN.md) | Codex HTTP 会话 |
| [agents-cli](agents-cli/README.zh-CN.md) | Codex 与 Qwen Code 的本地 HTTP API |
| [apply-patch](apply-patch/README.zh-CN.md) | 应用 Codex 格式文件补丁 |
| [qm-sandbox](qm-sandbox/README.zh-CN.md) | 基于 Node HTTP SDK 的 QM 工具 |
| [qm](qm/README.zh-CN.md) | 使用 SDK 后端的 QM Pi Agent 环境 |

### 文档、媒体与基准

| 模板 | 用途 |
| --- | --- |
| [document-tools](document-tools/README.zh-CN.md) | 文档转换、演示文稿与 PDF 导出 |
| [media-tools](media-tools/README.zh-CN.md) | FFmpeg 音视频处理 |
| [ocr](ocr/README.zh-CN.md) | 使用 Tesseract 识别英文文字 |
| [tau2-bench](tau2-bench/README.zh-CN.md) | Tau2 文本零售任务与评估 |
| [appworld](appworld/README.zh-CN.md) | AppWorld 任务与评估器 |

## 提供方内置运行时

这些条目使用所属平台的现成运行时，按其说明选择对应提供方：

| ID | Provider | 说明 |
| --- | --- | --- |
| base | alicloud-express | [README](docs/managed/base/README.zh-CN.md) |
| code-interpreter-v1 | alicloud-express | [README](docs/managed/code-interpreter-v1/README.zh-CN.md) |
| desktop | e2b | [README](docs/managed/desktop/README.zh-CN.md) |
| opensandbox-code-interpreter | opensandbox | [README](docs/managed/opensandbox-code-interpreter/README.zh-CN.md) |

## 定制与贡献

搜索模板：`abx template search python`。下载可编辑副本而不创建云资源：

```bash
abx template install python-hello --download-only --dir ./python-hello
```

源码与目录由本仓库维护，[`awesome-templates.yaml`](awesome-templates.yaml)供 CLI 和 Registry 读取。修改或新增模板前请阅读[贡献指南](CONTRIBUTING.zh-CN.md)与[模板规范](docs/template-spec.zh-CN.md)。模板问题请提交到 [Issues](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)。

## 许可证

[Apache-2.0](LICENSE)。各模板依赖的工具及资产还须遵循其上游许可证。
