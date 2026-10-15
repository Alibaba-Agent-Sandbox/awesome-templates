# 模板市场调研（2026-10）

## English summary

Survey date 2026-10-15, deepened the same day. Express `base` was probed with `abx create --template base` and then deleted. Verified: non-root `user` can `sudo -n` to uid 0, but `mount` is still denied; no KVM, FUSE, Docker socket, or GPU; 2 vCPU, ~2GB RAM, ~10G disk; Python 3.13.13 and Node 20.20.2; egress works; Xvfb + xdotool + scrot produced a PNG after apt install. Every OpenSandbox example, the E2B cookbook, CubeSandbox examples, and the Daytona/Modal/Vercel/Cloudflare galleries are mapped in the coverage matrix. Candidate templates: see `docs/template-backlog.json`. Wave 1 is CLI/service wrappers that fit Express. Wave 2 is a useful slice with a stated gap. Wave 3 needs another provider for the actual workload. Do not copy OpenSandbox or E2B Dockerfiles into this repo.

## 极速版探针

2026-10-15 在极速版模板 `base` 上实测（沙箱已删除）：用户 `user` uid 1000，`sudo -n` 可变成 uid 0，但 `sudo mount` 仍 permission denied；CapBnd/root CapEff = 00000000a80425fb（没有足够的 SYS_ADMIN 去做挂载）；无 /dev/kvm、无 /dev/fuse、无 /dev/dri、无 docker、无 docker.sock；2 vCPU，MemTotal 2143808 kB，rootfs 9.9G 可用约 9.3G；Debian 13，Python 3.13.13，Node v20.20.2，npm 10.8.2，git 2.47.3，gcc 与 make 在，没有 go/rust/java/ffmpeg/tesseract/pandoc/psql/Xvfb；/dev/shm 64M；出网访问 pypi.org 与 github.com 返回 HTTP 200；用户可以 bind 0.0.0.0:18080；`sudo apt-get install xvfb xdotool scrot openbox` 成功，`Xvfb :99` + `xdotool` + `scrot /tmp/s.png` 写出 2774 字节 PNG。未启动 openbox，所以窗口管理器会话未验证。未探测模板 `code-interpreter-v1`。

AK/SK 换票失败（FCSandbox `InvalidAction.NotFound`）。随后用 CLI `.env` 里的 `E2B_API_KEY` 作为 `ABX_SANDBOX_API_KEY`，基址是 `api.cn-hangzhou.e2b.fc.aliyuncs.com`，创建成功。密钥没有写入本文。

## 覆盖矩阵

状态：`exists` 目录已在 catalog；`new` 建议新建或已有 issue 但还没目录；`catalog-only` 只有平台/厂商 id，不在本仓库建 Dockerfile；`not-a-template` 不是模板。

| 来源 | 示例 | 模板 | 状态 | 备注 |
|---|---|---|---|---|
| OpenSandbox examples/ | claude-code | `claude-code` | exists |  |
| OpenSandbox examples/ | gemini-cli | `gemini` | exists |  |
| OpenSandbox examples/ | codex-cli | `codex` | exists |  |
| OpenSandbox examples/ | opencode | `opencode` | exists |  |
| OpenSandbox examples/ | qwen-code | `qwen-code` | exists |  |
| OpenSandbox examples/ | kimi-cli | `kimi-code` | new |  |
| OpenSandbox examples/ | langgraph | `not-a-template` | not-a-template | 图在宿主进程，沙箱只是工具后端。 |
| OpenSandbox examples/ | deep-agents | `deepagents` | new |  |
| OpenSandbox examples/ | google-adk | `not-a-template` | not-a-template | ADK 在宿主，工具进沙箱。 |
| OpenSandbox examples/ | openclaw | `openclaw` | exists |  |
| OpenSandbox examples/ | deer-flow | `not-a-template` | not-a-template | DeerFlow 2.1.0 自带 OpenSandboxProvider，编排在宿主。 |
| OpenSandbox examples/ | chrome | `chrome` | new |  |
| OpenSandbox examples/ | playwright | `browser-automation` | exists |  |
| OpenSandbox examples/ | desktop | `osworld` | new | 极速版切片是 osworld；E2B 的 desktop id 另记。 |
| OpenSandbox examples/ | vscode | `code-server` | new |  |
| OpenSandbox examples/ | code-interpreter | `opensandbox-code-interpreter` | catalog-only | 镜像短名由 OpenSandbox SDK 解析，不拷 Dockerfile。 |
| OpenSandbox examples/ | client-pool-schedule | `not-a-template` | not-a-template | 控制面 Resize API，不是镜像。 |
| OpenSandbox examples/ | aio-sandbox | `not-a-template` | not-a-template | 未钉的 ghcr.io/agent-infra/sandbox:latest，能力被 code-interpreter、osworld、code-server 拆开。 |
| OpenSandbox examples/ | agent-sandbox | `not-a-template` | not-a-template | kubernetes-sigs/agent-sandbox 是集群 CRD。 |
| OpenSandbox examples/ | aks-kata | `not-a-template` | not-a-template | 要 AKS 和 Kata VM。 |
| OpenSandbox examples/ | windows | `waa` | new | KVM/QEMU。极速版只保留远程客户端，见 waa。 |
| OpenSandbox examples/ | harbor-evaluation | `not-a-template` | not-a-template | 一个 trial 一个沙箱的编排器，试用现有模板，不单独做镜像。 |
| OpenSandbox examples/ | host-volume-mount | `not-a-template` | not-a-template | 极速版无宿主目录挂载。等价物是 files API 上传/下载。探针无 /dev/fuse，sudo mount 失败。 |
| OpenSandbox examples/ | docker-pvc-volume-mount | `not-a-template` | not-a-template | Docker named volume。极速版无 Docker。 |
| OpenSandbox examples/ | docker-ossfs-volume-mount | `not-a-template` | not-a-template | OSS FUSE。无 fuse 设备。对象存储要走 HTTPS SDK，不是挂载。 |
| OpenSandbox examples/ | rclone-volume-mount | `not-a-template` | not-a-template | 同样依赖 FUSE 或 CSI。 |
| OpenSandbox examples/ | kubernetes-pvc-volume-mount | `not-a-template` | not-a-template | PVC 是 Kubernetes 提供方的能力，不是模板。 |
| OpenSandbox examples/ | github-copilot-cli-sandbox | `copilot-cli` | new |  |
| OpenSandbox examples/ | microsoft-agent-framework | `not-a-template` | not-a-template | 宿主框架。 |
| OpenSandbox docs | apply-patch（文档页，examples/ 无目录） | `apply-patch` | new | CODEX_REF 仍是占位符。 |
| e2b-cookbook/examples | agentkit-coding-agent | `code-interpreter-v1` | catalog-only | 宿主 AgentKit + 解释器 |
| e2b-cookbook/examples | anthropic-claude-code-in-sandbox-js | `claude-code` | exists |  |
| e2b-cookbook/examples | anthropic-claude-code-in-sandbox-python | `claude-code` | exists |  |
| e2b-cookbook/examples | anthropic-computer-use-orangehrm-js | `osworld` | new | 桌面加浏览器 |
| e2b-cookbook/examples | anthropic-managed-agents | `not-a-template` | not-a-template | E2B webhook 模板，控制面不在极速版 |
| e2b-cookbook/examples | brainbase-universal-harness-bakeoff | `not-a-template` | not-a-template | 宿主 bake-off |
| e2b-cookbook/examples | claude-code-interpreter-js | `code-interpreter-v1` | catalog-only |  |
| e2b-cookbook/examples | claude-code-interpreter-python | `code-interpreter-v1` | catalog-only | README 404，按目录名归类 |
| e2b-cookbook/examples | claude-visualize-website-topics | `browser-automation` | exists | README 404，按目录名归类 |
| e2b-cookbook/examples | cleanup-paused-sandboxes | `not-a-template` | not-a-template | 生命周期 API |
| e2b-cookbook/examples | codestral-code-interpreter-js | `code-interpreter-v1` | catalog-only |  |
| e2b-cookbook/examples | codestral-code-interpreter-python | `code-interpreter-v1` | catalog-only | README 404 |
| e2b-cookbook/examples | crabbox-e2b-python | `not-a-template` | not-a-template | 宿主测试循环 |
| e2b-cookbook/examples | crewai-python | `not-a-template` | not-a-template | CrewAI 在宿主 |
| e2b-cookbook/examples | custom-sandbox-domain-proxy | `not-a-template` | not-a-template | 自定义域名是 provider 网络 |
| e2b-cookbook/examples | docker-in-e2b | `not-a-template` | not-a-template | 探针无 docker socket 且 mount 失败 |
| e2b-cookbook/examples | dspy-rlms-python | `code-interpreter-v1` | catalog-only | 宿主 DSPy |
| e2b-cookbook/examples | firecrawl-scrape-and-analyze-airbnb-data | `browser-automation` | exists | 抓取在浏览器或 HTTP，分析用解释器 |
| e2b-cookbook/examples | fireworks-code-interpreter-python | `code-interpreter-v1` | catalog-only | README 404 |
| e2b-cookbook/examples | flue-feedback-analyst-js | `not-a-template` | not-a-template | 宿主 Flue |
| e2b-cookbook/examples | groq-code-interpreter-js | `code-interpreter-v1` | catalog-only |  |
| e2b-cookbook/examples | groq-code-interpreter-python | `code-interpreter-v1` | catalog-only | README 404 |
| e2b-cookbook/examples | hello-world-js | `python-hello` | exists | JS 你好用 node-web 或 python-hello 的命令通道 |
| e2b-cookbook/examples | hello-world-python | `python-hello` | exists |  |
| e2b-cookbook/examples | hermes-incident-playbook-python | `hermes-agent` | exists |  |
| e2b-cookbook/examples | langchain-python | `code-interpreter-v1` | catalog-only | LangChain 在宿主 |
| e2b-cookbook/examples | langgraph-plan-and-execute-python | `not-a-template` | not-a-template | LangGraph 在宿主 |
| e2b-cookbook/examples | langgraph-python | `not-a-template` | not-a-template | 同上 |
| e2b-cookbook/examples | mcp-browserbase-js | `playwright-mcp` | new | 云浏览器不是本地 MCP |
| e2b-cookbook/examples | mcp-claude-code-js | `claude-code` | exists | MCP 客户端在 CLI 里 |
| e2b-cookbook/examples | mcp-client-js | `not-a-template` | not-a-template | 宿主 MCP 客户端 |
| e2b-cookbook/examples | mcp-custom-server-js | `not-a-template` | not-a-template | 示例服务器，不是产品模板 |
| e2b-cookbook/examples | mcp-custom-template-js | `not-a-template` | not-a-template | 教人建 E2B 模板 |
| e2b-cookbook/examples | mcp-groq-exa-js | `not-a-template` | not-a-template | 宿主 Groq + Exa |
| e2b-cookbook/examples | mcp-research-agent-js | `not-a-template` | not-a-template | 宿主研究 agent |
| e2b-cookbook/examples | muse-execution-backend-python | `muse` | new |  |
| e2b-cookbook/examples | nextjs-code-interpreter | `next-app` | new | 同时用 code-interpreter-v1 |
| e2b-cookbook/examples | openai-agents-api-python-sdk-webhook-managed | `codex-agent-api` | exists | webhook 形态相近但不是同一控制面 |
| e2b-cookbook/examples | openai-agents-api-python-sdk | `codex-agent-api` | exists |  |
| e2b-cookbook/examples | openai-agents-sdk | `not-a-template` | not-a-template | 宿主 Agents SDK |
| e2b-cookbook/examples | openai-codex-in-sandbox-js | `codex` | exists |  |
| e2b-cookbook/examples | openai-codex-in-sandbox-python | `codex` | exists |  |
| e2b-cookbook/examples | openai-image-analysis-js | `code-interpreter-v1` | catalog-only |  |
| e2b-cookbook/examples | openai-image-analysis-python | `code-interpreter-v1` | catalog-only | README 404 |
| e2b-cookbook/examples | openai-js | `code-interpreter-v1` | catalog-only |  |
| e2b-cookbook/examples | openai-ml-dataset-js | `code-interpreter-v1` | catalog-only |  |
| e2b-cookbook/examples | openai-ml-dataset-python | `code-interpreter-v1` | catalog-only | README 404 |
| e2b-cookbook/examples | openai-python | `code-interpreter-v1` | catalog-only | README 404 |
| e2b-cookbook/examples | opencode-e2b-workspace-js | `opencode` | exists |  |
| e2b-cookbook/examples | openenv-terminus-python | `swe` | new | 多轮修代码，不跑 Docker 评测 |
| e2b-cookbook/examples | pi-code-interpreter-js | `pi` | new |  |
| e2b-cookbook/examples | playwright-in-e2b | `browser-automation` | exists |  |
| e2b-cookbook/examples | pydantic-ai-python | `not-a-template` | not-a-template | 宿主 Pydantic AI |
| e2b-cookbook/examples | pydantic-ai-temporal-python | `not-a-template` | not-a-template | 宿主恢复逻辑 |
| e2b-cookbook/examples | sandbox-agent-sdk-js | `not-a-template` | not-a-template | 宿主 SDK |
| e2b-cookbook/examples | stirrup-python | `code-interpreter-v1` | catalog-only |  |
| e2b-cookbook/examples | tailcat-e2b | `not-a-template` | not-a-template | 宿主 Tailcat |
| e2b-cookbook/examples | together-ai-code-interpreter-js | `code-interpreter-v1` | catalog-only |  |
| e2b-cookbook/examples | together-ai-code-interpreter-python | `code-interpreter-v1` | catalog-only |  |
| e2b-cookbook/examples | trl-grpo-python | `not-a-template` | not-a-template | 训练循环要 GPU，极速版无 GPU |
| e2b-cookbook/examples | upload-dataset-code-interpreter | `code-interpreter-v1` | catalog-only | README 404，文件上传是 files API |
| e2b-cookbook/examples | vercel-ai-sdk-sandbox-js | `not-a-template` | not-a-template | 宿主 AI SDK，沙箱用 base |
| e2b-cookbook/examples | vercel-eve-feedback-analyst-js | `not-a-template` | not-a-template | 宿主 Eve |
| e2b-cookbook/examples | veris-e2b-js | `not-a-template` | not-a-template | 模拟服务在宿主编排 |
| e2b-cookbook/examples | watsonx-ai-code-interpreter-js | `code-interpreter-v1` | catalog-only |  |
| e2b-cookbook/examples | watsonx-ai-code-interpreter-python | `code-interpreter-v1` | catalog-only |  |
| E2B docs / repos | surf | `osworld` | new | 计算机使用示例，跑在 desktop 上 |
| E2B docs / repos | fragments | `next-app` | new | Next 应用脚手架，不是沙箱镜像 |
| E2B docs / repos | desktop repo | `desktop` | catalog-only | E2B Desktop SDK |
| E2B docs / repos | code-interpreter repo | `code-interpreter-v1` | catalog-only |  |
| E2B docs / repos | docs alias base | `base` | catalog-only |  |
| E2B docs / repos | docs alias code-interpreter-v1 | `code-interpreter-v1` | catalog-only |  |
| E2B docs / repos | docs alias desktop | `desktop` | catalog-only |  |
| E2B docs / repos | docs alias claude | `claude-code` | exists |  |
| E2B docs / repos | docs alias codex | `codex` | exists |  |
| E2B docs / repos | docs alias amp | `amp` | exists |  |
| E2B docs / repos | docs alias opencode | `opencode` | exists |  |
| E2B docs / repos | docs alias openclaw | `openclaw` | exists |  |
| E2B docs / repos | docs alias droid | `droid` | exists |  |
| E2B docs / repos | docs alias grok | `grok` | new |  |
| E2B docs / repos | docs alias pi | `pi` | new |  |
| E2B docs / repos | docs alias hermes | `hermes-agent` | exists |  |
| E2B docs / repos | docs alias devin | `devin` | new |  |
| E2B docs / repos | docs alias muse | `muse` | new |  |
| E2B docs / repos | docs alias prime | `prime-agent` | new |  |
| E2B docs / repos | docs alias kernel-browser | `browser-use` | new | 浏览器在 Kernel，不在沙箱 |
| E2B docs / repos | docs alias e2b/k3s | `k3s` | new |  |
| E2B docs / repos | docs alias android-16 | `android-world` | new | redroid，要 microVM |
| E2B docs / repos | docs alias cursor-agents | `cursor-agent` | new | 那是调度器，CLI 是另一件事 |
| E2B docs / repos | docs alias devin-outposts | `devin` | new | 企业调度器 |
| E2B docs / repos | docs alias E2B/claude-managed-agents-webhooks | `not-a-template` | not-a-template | webhook 控制面 |
| E2B docs / repos | docs recipe docker | `not-a-template` | not-a-template | 用户自己 build，极速版跑不了 |
| E2B docs / repos | docs recipe nextjs | `next-app` | new | 配方不是公开别名 |
| CubeSandbox | code-sandbox-quickstart | `code-interpreter-v1` | catalog-only | 用 sandbox-code:latest |
| CubeSandbox | browser-sandbox | `browser-automation` | exists | CDP 9000 |
| CubeSandbox | cubesandbox-base-nginx | `node-web` | exists | nginx 演示，服务形态相同 |
| CubeSandbox | ubuntu-desktop | `osworld` | new | GNOME+noVNC，要 MicroVM |
| CubeSandbox | claude-code-integration | `claude-code` | exists |  |
| CubeSandbox | openclaw-integration | `openclaw` | exists |  |
| CubeSandbox | opencode-plugin-sandbox | `opencode` | exists | 插件把 bash 送进沙箱 |
| CubeSandbox | pi-agent-integration | `pi` | new |  |
| CubeSandbox | langchain-integration | `not-a-template` | not-a-template | 宿主 |
| CubeSandbox | openai-agents-example | `not-a-template` | not-a-template | 宿主 Agents SDK |
| CubeSandbox | openai-agents-code-interpreter | `code-interpreter-v1` | catalog-only |  |
| CubeSandbox | mcp-gateway | `playwright-mcp` | new | 网关本身是控制面；浏览器 MCP 才是模板 |
| CubeSandbox | mini-rl-training | `swe` | new | RL 训练循环要 GPU/集群，评测切片归 swe |
| CubeSandbox | snapshot-rollback-clone | `not-a-template` | not-a-template | 平台快照 API |
| CubeSandbox | host-mount | `not-a-template` | not-a-template | 同 OpenSandbox host volume |
| CubeSandbox | volume | `not-a-template` | not-a-template | README 404，按目录名是卷插件 |
| CubeSandbox | network-policy | `not-a-template` | not-a-template | provider 网络 |
| CubeSandbox | route-aware-egress | `not-a-template` | not-a-template | provider 出口 |
| CubeSandbox | grpc-ingress | `not-a-template` | not-a-template | 入口 |
| CubeSandbox | ivshmem | `not-a-template` | not-a-template | 要 hypervisor 共享内存 |
| CubeSandbox | e2b-dev-sidecar | `not-a-template` | not-a-template | 开发边车 |
| CubeSandbox | cube-bench | `not-a-template` | not-a-template | 平台性能，不是应用模板 |
| CubeSandbox | run-code-env-inheritance | `code-interpreter-v1` | catalog-only | 解释器继承环境变量 |
| CubeSandbox | image sandbox-code:latest | `opensandbox-code-interpreter` | catalog-only | Cube 与 OpenSandbox 是不同镜像，都记在解释器行旁 |
| CubeSandbox | image sandbox-browser:latest | `browser-automation` | exists |  |
| CubeSandbox | image cubesandbox-base | `base` | catalog-only | 带 envd 的根文件系统 |
| Other galleries | daytona-small/medium/large | `base` | catalog-only | 规格档，不是 agent 名 |
| Other galleries | daytona default image agents | `claude-code` | exists | 镜像 README 还预装 codex、openclaw、opencode |
| Other galleries | daytona-gpu / windows / macos VM | `not-a-template` | not-a-template | 要 GPU、Windows 或 Apple 硬件 |
| Other galleries | modal Sandbox.create + Image | `code-interpreter-v1` | catalog-only | 没有公开 agent 目录 |
| Other galleries | modal Jupyter example | `code-interpreter-v1` | catalog-only |  |
| Other galleries | vercel universal image | `pi` | new | 同时还预装 claude-code、codex、opencode |
| Other galleries | vercel node/python/ubuntu/arch images | `base` | catalog-only | 滚动 tag，不能当 pin |
| Other galleries | vercel platform template | `next-app` | new | 预览服务器 |
| Other galleries | cloudflare examples/minimal | `python-hello` | exists |  |
| Other galleries | cloudflare examples/coding-agents/claude-code | `claude-code` | exists |  |
| Other galleries | cloudflare examples/coding-agents/codex | `codex` | exists |  |
| Other galleries | cloudflare examples/coding-agents/opencode | `opencode` | exists |  |
| Other galleries | cloudflare examples/coding-agents/pi | `pi` | new | README 指向 earendil-works/pi |
| Other galleries | cloudflare workspace/backup/checkpoint/s3 | `not-a-template` | not-a-template | 他们的持久化和对象存储；极速版用 files API，不能 FUSE |
| Other galleries | cloudflare terminal/process/preview | `node-web` | exists | 进程和预览端口 |

## 存储在 Agent Sandbox 里对应什么

OpenSandbox 的 host volume、Docker PVC、OSSFS、rclone、Kubernetes PVC，以及 Cube 的 host-mount、volume、Cloudflare 的 S3/checkpoint，都是提供方的卷，不是模板。极速版等价物是 SDK/CLI 的文件上传和下载。探针里没有 `/dev/fuse`，root 执行 `mount` 也被拒绝，所以不能在沙箱里做 FUSE 或绑定宿主目录。对象存储如果要做，应该是带密钥的 HTTPS 客户端命令，而不是挂载。快照、回滚、克隆、暂停是平台 API，同样不是模板目录。

## 并入说明

第一轮里单独列出的三个名字并进已有分析，没有丢掉：`linux-desktop` 的 Xvfb 切片就是 `osworld`；`mini-swe-agent` 是 `swe` 的 agent，不另开目录；`code-interpreter` 的瘦身实现记在 `code-interpreter-v1`，OpenSandbox 镜像记在 `opensandbox-code-interpreter`。

## 构建顺序

第一波是纯 CLI 或服务包装，极速版可以整份跑。第二波只能跑文中写明的子集。第三波的工作负载要别的 provider，极速版最多做远程客户端。`other` 是已有目录或厂商 id 的复核，不进这三波。

**第一波。** `claude-code`、`codex`、`codex-agent-api`、`opencode`、`amp`、`droid`、`gemini`、`qwen-code`、`deepseek-harness`、`openclaw`、`node-web`、`browser-automation`、`kimi-code`、`goose`、`pi`、`aider`、`browser-use`、`playwright-mcp`、`code-server`、`next-app`、`document-tools`、`dev-services`、`ocr`、`media-tools`、`tau2-bench`。

**第二波。** `hermes-agent`、`code-interpreter-v1`、`apply-patch`、`osworld`、`chrome`、`swe`、`polyglot-toolchain`、`cursor-agent`、`grok`、`copilot-cli`、`crush`、`cline`、`deepagents`、`stagehand`、`prime-agent`、`appworld`、`muse`、`devin`。

**第三波。** `waa`、`phone-sandbox`、`android-world`、`k3s`、`omarchy`、`qm`、`qm-sandbox`。

## 逐模板分析

锚点是二级标题的模板名。实施时以 `docs/template-backlog.json` 的字段为准，下面是同一份内容的说明。

## python-hello

**目的与用户。** 目录里最小的 Python 模板，用来验证 server、文件和命令通道，不是产品。

**能力。** `hello()` 返回纯文本问候。 端口：9000（agent-sandbox-server）。 文件与产物：无。 流式：不需要。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。不安装上游 CLI。保持目录，按现行基础镜像改 Dockerfile，不要再写 CMD。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：1–2 vCPU，512MB 足够。 SDK：`Sandbox.create` 之后调用命名命令（`hello`）。依赖模板：无。

**需要。** 无密钥、无 GPU、无 KVM、无 Docker、无显示器。

**极速版。** `yes`。限制因素：没有产品限制。 能跑的子集：整份模板都能在极速版跑。 其余：不需要别的 provider。

**上游与调用。** 本仓库。 无头形态：hello。

**结论。** 状态 exists，批次 other，优先级 P2，issue #21。验收用的最小模板，已经存在。 来源：catalog。

## base

**目的与用户。** 平台模板 id `base`，也是 E2B 不传 template 时的默认沙箱。给所有别的模板当参照，不在本仓库里再做一个同名目录。

**能力。** 没有命名命令。调用方用 `abx exec` 或 SDK `commands.run`。 端口：49983（envd，创建时返回的 URL 带这个端口）。 文件与产物：空的 /home/user。 流式：exec 支持流式 stdout。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。不要新建目录。文档写清如何 `abx create --template base`。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：实测 2 vCPU，约 2GB 内存，约 10G rootfs。 SDK：`Sandbox.create` 之后调用命名命令（`exec`）。依赖模板：无。

**需要。** 极速版 API key。无 GPU/KVM/Docker。

**极速版。** `yes`。限制因素：这是平台镜像，本仓库 Dockerfile 改变不了它。 能跑的子集：实测内容见文首探针。 其余：E2B 的 `base` 是另一块 Debian 镜像（带 gh、Yarn），不要写成同一份软件清单。

**上游与调用。** 平台镜像；E2B 文档 base image，Dockerfile templates/base/e2b.Dockerfile。 无头形态：abx exec <id> -- <argv>。

**结论。** 状态 catalog-only，批次 other，优先级 P1，issue #31。目录外的平台模板，issue #31 只做文档和核实。 来源：express-probe, e2b-docs。

## claude-code

**目的与用户。** Anthropic 的编码 CLI。用户是要在沙箱里改仓库的 agent 调用方。

**能力。** `claude(prompt, resume='', output_format='text') -> {stdout, stderr, exit_code}`。对应 `claude --dangerously-skip-permissions -p`。 端口：9000。 文件与产物：工作区 diff，可用 files API 取出。 流式：`--output-format stream-json` 时需要流式 stdout。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。钉死 `@anthropic-ai/claude-code@<version>`（以目录里已有 pin 为准，升级要改 pin 并写进构建日志）。Node 20 够用则不要另装 Node 22。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU，2GB。 SDK：`Sandbox.create` 之后调用命名命令（`claude`）。依赖模板：无。

**需要。** ANTHROPIC_API_KEY。无 GPU/KVM/Docker/显示器。

**极速版。** `yes`。限制因素：本环境没有 Anthropic key，L3 不能在这里宣称通过。 能跑的子集：整条 CLI 都适合极速版。 其余：E2B 公开别名 `claude`。OpenSandbox 示例是在 code-interpreter 里 `npm i -g @latest`，不要学未钉版本。

**上游与调用。** E2B docs/agents/claude-code.md（2026-10-15）；目录已有。 无头形态：claude --dangerously-skip-permissions -p "<prompt>"。

**结论。** 状态 exists，批次 1，优先级 P0，issue #15。已有目录。这一波只按 spec 复核，不新建。 来源：opensandbox:claude-code, e2b:claude, cloudflare:coding-agents/claude-code, cookbook:anthropic-claude-code-*。

## codex

**目的与用户。** OpenAI Codex 编码 CLI。

**能力。** `codex(prompt) -> {stdout, stderr, exit_code}`，调用 `codex exec --full-auto`。 端口：9000。 文件与产物：git diff。 流式：JSONL 事件需要流式。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。钉 `@openai/codex@<已有 pin>`。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU，2GB。 SDK：`Sandbox.create` 之后调用命名命令（`codex`）。依赖模板：无。

**需要。** CODEX_API_KEY 或 OPENAI_API_KEY（以已有 template.yaml 为准）。

**极速版。** `yes`。限制因素：无平台限制。 能跑的子集：整条 CLI。 其余：E2B 别名 `codex`；Cloudflare examples/coding-agents/codex；Cube 没有单独镜像。

**上游与调用。** https://docs.e2b.dev/agents/codex.md 无头形态：codex exec --full-auto "<prompt>"。

**结论。** 状态 exists，批次 1，优先级 P0，issue #16。已有。 来源：opensandbox:codex-cli, e2b:codex, cloudflare:codex, cookbook:openai-codex-*。

## codex-agent-api

**目的与用户。** 用 Codex CLI 提供一个兼容 OpenAI Agents API 的本地服务。

**能力。** `serve_start() -> {port, url}`，然后 HTTP 创建 session。 端口：服务端口加 9000。 文件与产物：session 日志。 流式：Agents API 流式响应。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。沿用目录里的 pin。start_cmd 只启动 agent-sandbox-server；Agents 服务由命名命令拉起。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU，2GB。 SDK：`Sandbox.create` 之后调用命名命令（`serve_start`）。依赖模板：codex。

**需要。** OpenAI/Codex key。

**极速版。** `yes`。限制因素：无。 能跑的子集：整个服务都能在单容器里跑。 其余：E2B cookbook 的 openai-agents-api 是控制面示例，不是另一块镜像。

**上游与调用。** 本仓库目录。 无头形态：命名命令启动后 curl 健康检查。

**结论。** 状态 exists，批次 1，优先级 P1，issue #23。已有服务型模板。 来源：cookbook:openai-agents-api-*, catalog。

## opencode

**目的与用户。** 多模型编码 CLI。

**能力。** `opencode(prompt, model='') -> {stdout, stderr, exit_code}`，即 `opencode run`。可选 `opencode_serve()` 监听 4096。 端口：4096 仅在 serve 模式。 文件与产物：diff。 流式：serve 是 HTTP，不是必须。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。目录钉 `opencode-ai@1.19.0`。升级版本另开变更，不要在本次调研里改 pin。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU，2GB。 SDK：`Sandbox.create` 之后调用命名命令（`opencode`）。依赖模板：无。

**需要。** ANTHROPIC_API_KEY 或其他 provider key。

**极速版。** `yes`。限制因素：experimental，缺密钥 e2e。 能跑的子集：整条 CLI。 其余：E2B 别名 `opencode`；Cloudflare examples/coding-agents/opencode。

**上游与调用。** https://docs.e2b.dev/agents/opencode.md 无头形态：opencode run "<prompt>"。

**结论。** 状态 exists，批次 1，优先级 P0，issue #17。已有 experimental。 来源：opensandbox:opencode, e2b:opencode, cloudflare:opencode, cube:opencode-plugin-sandbox。

## amp

**目的与用户。** Sourcegraph Amp 编码 CLI。

**能力。** `amp(prompt) -> {stdout, stderr, exit_code}`，`amp --dangerously-allow-all -x`。 端口：9000。 文件与产物：diff。 流式：`--stream-json`。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。保持目录中的 npm pin。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU，2GB。 SDK：`Sandbox.create` 之后调用命名命令（`amp`）。依赖模板：无。

**需要。** AMP_API_KEY。

**极速版。** `yes`。限制因素：无平台限制，缺密钥。 能跑的子集：整条 CLI。 其余：E2B 别名 `amp`。

**上游与调用。** https://docs.e2b.dev/agents/amp.md 无头形态：amp --dangerously-allow-all -x "<prompt>"。

**结论。** 状态 exists，批次 1，优先级 P1，issue #18。已有 experimental。 来源：e2b:amp, catalog。

## droid

**目的与用户。** Factory 的编码 CLI。

**能力。** `droid(prompt) -> {stdout, stderr, exit_code}`，`droid exec`。 端口：9000。 文件与产物：diff。 流式：可选。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。目录钉 `@factory/cli@0.241.1`。E2B 文档用 `--auto low`，和目录里的 flag 是否一致要在复核时对 `--help`。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU，2GB。 SDK：`Sandbox.create` 之后调用命名命令（`droid`）。依赖模板：无。

**需要。** FACTORY_API_KEY。

**极速版。** `yes`。限制因素：无。 能跑的子集：整条 CLI。 其余：E2B 别名 `droid`。

**上游与调用。** https://docs.e2b.dev/agents/droid.md 无头形态：droid exec --auto low "<prompt>"。

**结论。** 状态 exists，批次 1，优先级 P1，issue #19。已有 experimental。 来源：e2b:droid, catalog。

## gemini

**目的与用户。** Google Gemini 终端编码 CLI。

**能力。** `gemini(prompt, model='') -> str`，`gemini -p --yolo`。 端口：9000。 文件与产物：diff。 流式：不强制。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。已钉 `@google/gemini-cli@0.64.0`。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU，2GB。 SDK：`Sandbox.create` 之后调用命名命令（`gemini`）。依赖模板：无。

**需要。** GEMINI_API_KEY。

**极速版。** `yes`。限制因素：缺带 ABX_E2E_OK 的密钥记录，不能标 official。 能跑的子集：整条 CLI。 其余：OpenSandbox gemini-cli 示例未钉版本。

**上游与调用。** 本仓库 gemini/；OpenSandbox examples/gemini-cli。 无头形态：gemini -p "<prompt>" --yolo。

**结论。** 状态 exists，批次 1，优先级 P0，issue #30。已有 experimental。 来源：opensandbox:gemini-cli, catalog。

## qwen-code

**目的与用户。** 通义千问编码 CLI，DashScope 兼容。

**能力。** `qwen(prompt) -> {stdout, stderr, exit_code}`。 端口：9000。 文件与产物：diff。 流式：可选。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。保持目录 pin。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU，2GB。 SDK：`Sandbox.create` 之后调用命名命令（`qwen`）。依赖模板：无。

**需要。** DASHSCOPE_API_KEY 或目录里声明的变量。本环境有 OpenAI 兼容端点时可做 L3，是否被该 CLI 接受要在实现时试。

**极速版。** `yes`。限制因素：无平台限制。 能跑的子集：整条 CLI。 其余：OpenSandbox qwen-code 示例。

**上游与调用。** 本仓库。 无头形态：qwen 的无头参数以目录 commands.py 为准。

**结论。** 状态 exists，批次 1，优先级 P0，issue #26。已有。 来源：opensandbox:qwen-code, catalog。

## deepseek-harness

**目的与用户。** 用 DeepSeek 兼容端点做编码回合。

**能力。** 以目录 commands.py 为准，返回 stdout。 端口：9000。 文件与产物：工作区。 流式：可选。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。保持 pin。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU，2GB。 SDK：`Sandbox.create` 之后调用命名命令（`deepseek`）。依赖模板：无。

**需要。** DeepSeek 或兼容 key。

**极速版。** `yes`。限制因素：无。 能跑的子集：整份。 其余：无对应 E2B 别名。

**上游与调用。** 本仓库。 无头形态：见 commands.py。

**结论。** 状态 exists，批次 1，优先级 P1，issue #27。已有。 来源：catalog。

## openclaw

**目的与用户。** OpenClaw 网关，给浏览器或频道接一个常驻 agent。

**能力。** `gateway_start(token, port=18789) -> {url}`。不是单次 `-p`。 端口：18789。 文件与产物：~/.openclaw 配置。 流式：WebSocket，不是命令 stdout。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。钉 openclaw 版本，不要 `ghcr.io/openclaw/openclaw:latest`。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU，2GB。 SDK：`Sandbox.create` 之后调用命名命令（`gateway_start`）。依赖模板：无。

**需要。** 模型 key。token 来自环境变量。

**极速版。** `yes`。限制因素：常驻进程必须由命名命令拉起，不能写 ENTRYPOINT。 能跑的子集：gateway 本身可以在极速版跑。 其余：E2B 别名 `openclaw`；OpenSandbox 用未钉的 ghcr 镜像。

**上游与调用。** https://docs.e2b.dev/agents/openclaw/openclaw-gateway.md 无头形态：openclaw gateway --allow-unconfigured --bind lan --auth token --port 18789。

**结论。** 状态 exists，批次 1，优先级 P0，issue #20。已有。 来源：opensandbox:openclaw, e2b:openclaw, cube:openclaw-integration。

## hermes-agent

**目的与用户。** Nous Research 的可成长 agent。目录描述写明当前只做聊天补全、不注册工具。升级目标是真 CLI。

**能力。** 升级后 `hermes(prompt, provider, model) -> {stdout, stderr, exit_code}`，即 `hermes chat -Q --yolo -q`。 端口：9000。 文件与产物：~/.hermes/skills 与 memories。 流式：不强制。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。钉 GitHub release v0.22.1（2026-10-14，MIT）。安装命令以该 tag 的 README 为准，本次未打开 README，安装行 unverified。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU，2GB。 SDK：`Sandbox.create` 之后调用命名命令（`hermes`）。依赖模板：无。

**需要。** provider key，E2B 示例是 OPENROUTER_API_KEY。

**极速版。** `partial`。限制因素：现行目录没有 CLI。 能跑的子集：先把 v0.22.1 的 `hermes` 二进制放进现有目录，不要新建名字。 其余：E2B 别名 `hermes`。cookbook hermes-incident-playbook 是宿主脚本。

**上游与调用。** https://github.com/NousResearch/hermes-agent v0.22.1；https://docs.e2b.dev/agents/hermes.md 无头形态：hermes chat -Q --yolo -q "<prompt>"。

**结论。** 状态 exists，批次 2，优先级 P0，issue #28。升级已有模板，不是新目录。 来源：e2b:hermes, cookbook:hermes-incident-playbook-python, catalog。

## qoder

**目的与用户。** 目录描述写明只执行本地脚本，没有安装 Qoder CLI。

**能力。** `qoder_run` 跑本地脚本。若上游给出可钉的无头 CLI，再加 `qoder(prompt)`。 端口：9000。 文件与产物：脚本输出。 流式：不需要。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。没有可钉的 Qoder 安装物之前不要假装装了 CLI。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU，2GB。 SDK：`Sandbox.create` 之后调用命名命令（`qoder_run`）。依赖模板：无。

**需要。** CLI 出现后才需要 key。

**极速版。** `partial`。限制因素：上游安装 unverified。 能跑的子集：现在只能跑本地脚本。 其余：无。

**上游与调用。** 本仓库描述。 无头形态：qoder_run。

**结论。** 状态 exists，批次 other，优先级 P2，issue #24。已有，但是空 CLI。 来源：catalog。

## agents-cli

**目的与用户。** 给 Codex 和 Qwen 的 Agents API 占位。镜像里没有这两个 CLI。

**能力。** 保持现有命令。真正要跑 CLI 时用 `codex` 和 `qwen-code`。 端口：9000。 文件与产物：无。 流式：无。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。不要在这个目录里再装一份未钉的 CLI。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU。 SDK：`Sandbox.create` 之后调用命名命令（`agents`）。依赖模板：codex, qwen-code。

**需要。** 无，直到它真的调用 CLI。

**极速版。** `partial`。限制因素：名不副实。 能跑的子集：健康检查可以过。产品调用走另外两个模板。 其余：无。

**上游与调用。** 本仓库。 无头形态：见 commands.py。

**结论。** 状态 exists，批次 other，优先级 P2，issue #25。已有占位。 来源：catalog。

## node-web

**目的与用户。** 跑 Express/Fastify 一类 Node 服务。不是 Next/Vite 开发服务器。

**能力。** `start(script)` 拉起用户进程并返回端口。 端口：由参数指定，外加 9000。 文件与产物：应用目录。 流式：服务日志。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。Node 20 已在基础镜像里。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU，2GB。 SDK：`Sandbox.create` 之后调用命名命令（`start`）。依赖模板：无。

**需要。** 无密钥。

**极速版。** `yes`。限制因素：无。 能跑的子集：整份。 其余：Vercel 的 Next 脚手架见 `next-app`。

**上游与调用。** 本仓库。 无头形态：node server.js。

**结论。** 状态 exists，批次 1，优先级 P1，issue #29。已有。 来源：catalog, cloudflare:minimal。

## browser-automation

**目的与用户。** 无头 Chromium，给抓取和 UI 检查用。

**能力。** 已有 Playwright 命令。返回标题、正文或截图路径。 端口：9000。CDP 若暴露，用独立端口。 文件与产物：截图 PNG。 流式：不强制。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。钉 Playwright 与对应 Chromium。`/dev/shm` 实测只有 64M，启动参数加 `--disable-dev-shm-usage`。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU，2GB。 SDK：`Sandbox.create` 之后调用命名命令（`browse`）。依赖模板：无。

**需要。** 无模型密钥。无 GPU/KVM/Docker。

**极速版。** `yes`。限制因素：shm 64M 已实测，是浏览器崩溃的常见原因。 能跑的子集：无头 Playwright 可以跑。带 VNC 的 Chrome 归 `chrome`。 其余：OpenSandbox playwright:latest 未钉；Cube sandbox-browser 是 MicroVM 里的 CDP。

**上游与调用。** 本仓库；OpenSandbox examples/playwright；Cube examples/browser-sandbox。 无头形态：playwright chromium headless。

**结论。** 状态 exists，批次 1，优先级 P0，issue #22。已有，浏览器类示例都先落到这里。 来源：opensandbox:playwright, cube:browser-sandbox, cookbook:playwright-in-e2b。

## code-interpreter-v1

**目的与用户。** 平台模板 id，对齐 E2B `code-interpreter-v1`：在沙箱里执行模型写的代码并拿回 stdout。

**能力。** 若平台镜像已带解释器，文档化 SDK `run_code`。若没有，在目录里提供 `execute_code(language, code) -> {stdout, stderr, error}` 和 `list_runtimes()`。本次没有对这个 template id 做 exec，镜像里有什么 unverified。 端口：E2B 是 49999。极速版是否同样，unverified。 文件与产物：代码生成的图表写入 /tmp 再由 files API 读出。 流式：长输出要流式。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。不要复制 E2B 或 OpenSandbox 的 Dockerfile。若要自建，FROM 平台基础镜像，只钉 jupyter-server==2.20.0、ipykernel==6.31.0、pandas==2.2.3、numpy==2.3.5、matplotlib==3.10.9、pillow==12.3.0（2026-10-15 从 e2b-dev/code-interpreter main 的 requirements.txt 读到）。先不要装 spacy/opencv/librosa。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU，2GB。科学栈容易吃掉 10G 磁盘。 SDK：`Sandbox.create` 之后调用命名命令（`execute_code`, `list_runtimes`）。依赖模板：无。

**需要。** 执行代码本身不要密钥。

**极速版。** `partial`。限制因素：未探测该 template id；全量 E2B 依赖对 10G 磁盘 unverified。 能跑的子集：瘦身 Python 解释器。Java/Go 多版本不要塞进第一版。 其余：OpenSandbox `code-interpreter:v1.1.0` 走 issue #34，不要和这个 id 混成一块镜像。

**上游与调用。** E2B code-interpreter；OpenSandbox sandbox-images README。 无头形态：execute_code。

**结论。** 状态 catalog-only，批次 2，优先级 P0，issue #32。每个厂商都有一块执行代码的镜像。先核实平台 id，缺了再自建瘦身版。 来源：e2b:code-interpreter-v1, cookbook:hello-world-*, cookbook:openai-*, cookbook:groq-*, cookbook:langchain-python, cookbook:langgraph-*, modal:sandbox, cloudflare:code-interpreter-docs, daytona:default-snapshot。

## opensandbox-code-interpreter

**目的与用户。** OpenSandbox 发布的镜像，不是极速版目录。

**能力。** OpenSandbox Code Interpreter SDK 执行 Python/Java/TS/Go。 端口：Jupyter 127.0.0.1:44771，不映射到宿主机。 文件与产物：内核工作目录。 流式：SDK 结果。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。不要把 Dockerfile 拷进本仓库。文档写镜像 `sandbox-registry.cn-zhangjiakou.cr.aliyuncs.com/opensandbox/code-interpreter:v1.1.0`。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：由 OpenSandbox 集群决定。 SDK：`Sandbox.create` 之后调用命名命令（`execute_code`）。依赖模板：无。

**需要。** SANDBOX_DOMAIN、SANDBOX_API_KEY。

**极速版。** `partial`。限制因素：极速版 `abx template install` 不会把这块镜像注册成 OpenSandbox 的短名。 能跑的子集：同一能力在极速版用 `code-interpreter-v1` 的瘦身实现。 其余：只有 OpenSandbox provider。

**上游与调用。** examples/code-interpreter/main.py 默认镜像 v1.1.0；sandbox-images README。 无头形态：CodeInterpreter SDK。

**结论。** 状态 catalog-only，批次 other，优先级 P1，issue #34。目录外镜像。 来源：opensandbox:code-interpreter。

## desktop

**目的与用户。** E2B 公开模板 `desktop`：Ubuntu 22.04 XFCE、noVNC 6080、LibreOffice、xdotool、scrot。

**能力。** Desktop SDK `screenshot`、鼠标键盘、`stream.start()`。 端口：6080。 文件与产物：截图。 流式：VNC。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。不要在本仓库复制 E2B desktop Dockerfile 来冒充这个 id。极速版的桌面切片用 `osworld`。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：E2B 侧建议高于 base 的 512MB。 SDK：`Sandbox.create` 之后调用命名命令（`screenshot`）。依赖模板：无。

**需要。** 无 KVM。要虚拟显示。

**极速版。** `partial`。限制因素：本仓库没有 E2B key 时不能宣称在 E2B 上跑通。issue 写明了这一点。 能跑的子集：见 osworld。 其余：E2B。Cube 的 ubuntu-desktop 是另一块要自己构建的 GNOME 镜像。

**上游与调用。** https://docs.e2b.dev/template/examples/desktop.md 无头形态：sandbox.screenshot()。

**结论。** 状态 catalog-only，批次 other，优先级 P2，issue #33。只做目录外文档。 来源：e2b:desktop, e2b-dev/desktop, e2b-dev/surf。

## kimi-code

**目的与用户。** Moonshot 现行编码 CLI。用户是要接 Kimi 模型的编程 agent。

**能力。** `kimi(prompt) -> {stdout, stderr, exit_code}`。 端口：9000。 文件与产物：diff。 流式：`--output-format stream-json` 时要流式，flag 在 2.2.0 上核对。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。基础镜像是 Node 20。另装 Node ≥22.19，再 `npm install -g @moonshot-ai/kimi-code@2.2.0`（release 2026-10-14，MIT）。不要用 code.kimi.com 的脚本，也不要 `pip install kimi-cli`（旧仓库已归档）。OpenSandbox README 已改称 Kimi Code CLI，但更早的 main.py 仍是未钉的 pip。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU，2GB。 SDK：`Sandbox.create` 之后调用命名命令（`kimi`）。依赖模板：无。

**需要。** Moonshot API key，环境变量名在 2.2.0 文档里核对，本次 unverified。无 GPU/KVM/Docker/显示器。

**极速版。** `yes`。限制因素：Node 版本，可在镜像构建时解决。 能跑的子集：整条 CLI。 其余：不需要。

**上游与调用。** https://github.com/MoonshotAI/kimi-code @moonshot-ai/kimi-code@2.2.0 无头形态：kimi -p "<prompt>"。

**结论。** 状态 new，批次 1，优先级 P0，issue 本次新建。OpenSandbox 有示例，目录里没有 Moonshot CLI。 来源：opensandbox:kimi-cli。

## goose

**目的与用户。** AAIF 的终端 agent，也能做非编码任务。

**能力。** `goose(text) -> {stdout, stderr, exit_code}`，即 `goose run -t`。 端口：9000。 文件与产物：工作区改动。 流式：不强制。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。下载 https://github.com/block/goose/releases/download/v1.54.0/goose-x86_64-unknown-linux-gnu.tar.bz2 （80890920 字节）。不要 vulkan/cuda，不要 stable/download_cli.sh。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU，2GB。压缩包约 80MB。 SDK：`Sandbox.create` 之后调用命名命令（`goose`）。依赖模板：无。

**需要。** 所选 provider 的 API key。无 GPU。

**极速版。** `yes`。限制因素：无平台限制。 能跑的子集：整条 CLI。 其余：不需要。

**上游与调用。** https://github.com/block/goose v1.54.0 Apache-2.0 无头形态：goose run -t "<text>"。

**结论。** 状态 new，批次 1，优先级 P0，issue 本次新建。有钉死的 Linux 包和无头命令。 来源：upstream:block/goose。

## pi

**目的与用户。** 小体积终端编码 agent。E2B、Vercel universal、Cloudflare、Cube 都把它当一等公民。

**能力。** `pi(prompt) -> {stdout, stderr, exit_code}`。 端口：9000。 文件与产物：diff。 流式：JSON 事件，Cloudflare 说明失败时仍可能 exit 0，调用方要解析事件。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。优先 https://github.com/badlogic/pi-mono/releases/download/v1.2.0/pi-linux-x64.tar.gz （42611136 字节）。是否自带 Node unverified。否则 Node ≥22.19 且 `npm install -g --ignore-scripts @earendil-works/pi-coding-agent@1.2.0`。Cloudflare README 指向 https://github.com/earendil-works/pi ，和 badlogic/pi-mono 是否同一远程 unverified。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU，2GB。 SDK：`Sandbox.create` 之后调用命名命令（`pi`）。依赖模板：无。

**需要。** ANTHROPIC_API_KEY 或其他 provider。无权限弹窗。

**极速版。** `yes`。限制因素：无 KVM/Docker 需求。本目录不会变成 E2B 别名 `pi`。 能跑的子集：整条 CLI。 其余：E2B 别名只在 E2B 账号里存在。

**上游与调用。** pi-mono v1.2.0 MIT；https://docs.e2b.dev/agents/pi.md；https://pi.dev/docs/latest/cli 无头形态：pi -p "<prompt>"（pi.dev 写 --print，以 v1.2.0 --help 为准）。

**结论。** 状态 new，批次 1，优先级 P0，issue #41。issue #41 已存在，不新建 issue。 来源：e2b:pi, cloudflare:coding-agents/pi, cube:pi-agent-integration, cookbook:pi-code-interpreter-js, vercel:universal。

## aider

**目的与用户。** 在 git 仓库里改完文件就退出的结对编程 CLI。

**能力。** `aider(prompt) -> {stdout, stderr, exit_code}`，工作目录必须是 git 仓库。 端口：9000。 文件与产物：git diff。 流式：不需要。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。`pip install aider-chat==0.86.0`（release 2025-08-09，Apache-2.0）。仓库 2026-05-22 后无推送。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU，2GB。 SDK：`Sandbox.create` 之后调用命名命令（`aider`）。依赖模板：无。

**需要。** OPENAI_API_KEY 或 ANTHROPIC_API_KEY。

**极速版。** `yes`。限制因素：上游停更，不是平台限制。 能跑的子集：整条 CLI。 其余：不需要。

**上游与调用。** https://github.com/Aider-AI/aider v0.86.0 无头形态：aider --yes --message "<prompt>"。

**结论。** 状态 new，批次 1，优先级 P1，issue 本次新建。安装钉得死，形态和现有 CLI 一样。 来源：upstream:Aider-AI/aider。

## browser-use

**目的与用户。** 在无头 Chromium 上跑浏览器 agent，而不是只暴露 Playwright 原语。

**能力。** `browser_use(task) -> {result, final_url}`。0.13.11 的构造参数从该 tag README 抄，不要凭记忆。 端口：9000。 文件与产物：截图。 流式：步骤日志建议流式。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。`pip install browser-use==0.13.11`，Chromium 用它依赖的 Playwright 版本，加 `--disable-dev-shm-usage`。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU，2GB。shm 64M 已实测。 SDK：`Sandbox.create` 之后调用命名命令（`browser_use`）。依赖模板：browser-automation。

**需要。** 模型 key。无 GPU/KVM/Docker。

**极速版。** `yes`。限制因素：shm。 能跑的子集：本地无头 Chromium。不要依赖 Browser Use Cloud。 其余：E2B `kernel-browser` 把浏览器放在 Kernel，我们没有 Kernel。

**上游与调用。** https://github.com/browser-use/browser-use 0.13.11 MIT 无头形态：Python Agent(task=...)。

**结论。** 状态 new，批次 1，优先级 P0，issue 本次新建。118k stars，和 browser-automation 互补。 来源：e2b:kernel-browser, upstream:browser-use。

## playwright-mcp

**目的与用户。** 让编码 CLI 通过 MCP 驱动浏览器。

**能力。** `mcp_start() -> {port}`。若 browser-automation 镜像装得下，把命令加进那个目录，不要第二份 Chromium。 端口：默认 8931，以 `@playwright/mcp@0.0.83 --help` 为准。 文件与产物：无。 流式：MCP 传输。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。`npm install -g @playwright/mcp@0.0.83`（2026-09-28，Apache-2.0）。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU，2GB。 SDK：`Sandbox.create` 之后调用命名命令（`mcp_start`）。依赖模板：browser-automation。

**需要。** Chromium。模板内不要模型 key。

**极速版。** `yes`。限制因素：shm 64M。 能跑的子集：无头 MCP。 其余：E2B MCP gateway 是他们的托管目录，不是这块二进制。

**上游与调用。** https://github.com/microsoft/playwright-mcp v0.0.83 无头形态：npx @playwright/mcp@0.0.83 --headless --port 8931。

**结论。** 状态 new，批次 1，优先级 P1，issue 本次新建。目录里的浏览器模板不会说 MCP。 来源：cookbook:mcp-browserbase-js, cookbook:mcp-claude-code-js, upstream:playwright-mcp。

## code-server

**目的与用户。** 浏览器里的 VS Code，给人不想用终端的调试。

**能力。** `code_server_start() -> {port: 8443}`。 端口：8443。 文件与产物：工作区。 流式：不需要。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。解压 code-server-4.141.0-linux-amd64.tar.gz（239926515 字节，MIT，2026-10-08）。密码来自环境变量。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU，2GB。压缩包 240MB，加上基础镜像后是否仍低于 10G，构建时看 df。 SDK：`Sandbox.create` 之后调用命名命令（`code_server_start`）。依赖模板：无。

**需要。** 密码。无 GPU/KVM/Docker/显示器。

**极速版。** `yes`。限制因素：体积。 能跑的子集：整个 code-server。 其余：OpenSandbox vscode:latest 未钉，不要 FROM 它。

**上游与调用。** https://github.com/coder/code-server v4.141.0 无头形态：code-server --bind-addr 0.0.0.0:8443 --auth password。

**结论。** 状态 new，批次 1，优先级 P1，issue 本次新建。OpenSandbox 的 vscode 示例在极速版没有对应物。 来源：opensandbox:vscode。

## next-app

**目的与用户。** 给 agent 一个能预览的前端开发服务器。node-web 只是通用 Node 进程，没有脚手架。

**能力。** `dev_start(kind) -> {port, url}`，kind 为 next 或 vite。`scaffold()` 写出最小工程。 端口：3000 或 5173。 文件与产物：应用目录。 流式：dev server 日志。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。`npm install -g` 不适合。在镜像里 `npm install next@<pin>` 与 `vite@<pin>`，pin 取构建当天的 dist-tag 并写进日志，不要用 latest 当永久版本。Node 20 已有。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU，2GB。 SDK：`Sandbox.create` 之后调用命名命令（`dev_start`）。依赖模板：node-web。

**需要。** 无密钥。

**极速版。** `yes`。限制因素：HMR 的 websocket 要平台能转发该端口，转发行为 unverified。 能跑的子集：能起服务并返回端口即可，不保证 HMR。 其余：Vercel 平台模板还会部署上线，那一步不在沙箱里。

**上游与调用。** Vercel platform template 文档；E2B template examples/nextjs 是配方不是公开别名；fragments 是应用模板不是沙箱。 无头形态：next dev --port 3000 或 vite --host 0.0.0.0。

**结论。** 状态 new，批次 1，优先级 P1，issue 本次新建。预览服务器是 Vercel/fragments 一类例子里真正缺的运行时。 来源：e2b:template/examples/nextjs, e2b-dev/fragments, cookbook:nextjs-code-interpreter, vercel:platform-template。

## document-tools

**目的与用户。** 把 markdown/html 转成 docx、pdf、幻灯片。

**能力。** `convert(input_path, output_format) -> {output_path}`。 端口：9000。 文件与产物：输入输出都在 /home/user。 流式：不需要。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。apt 钉 pandoc 与 libreoffice-writer 的 Debian 13 版本，写进构建日志。soffice 使用独立 HOME。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU，2GB。LibreOffice 体积要在构建时看 df。 SDK：`Sandbox.create` 之后调用命名命令（`convert`）。依赖模板：无。

**需要。** 无密钥、无显示器。

**极速版。** `yes`。限制因素：非 root 跑 soffice 本次未在极速版执行，只验证了 apt 通道和 Xvfb。 能跑的子集：pandoc 纯文本转换一定能做；soffice 作为第二步。 其余：E2B desktop 带了 LibreOffice 但是 GUI。

**上游与调用。** Debian pandoc（GPL-2.0）与 LibreOffice（MPL-2.0）。 无头形态：pandoc 或 soffice --headless --convert-to。

**结论。** 状态 new，批次 1，优先级 P1，issue 本次新建。文档转换不需要桌面会话。 来源：e2b:desktop。

## dev-services

**目的与用户。** 给应用提供数据库，替代 Docker Compose。

**能力。** `services_start() -> {postgres:5432, redis:6379}`，`services_stop()`。 端口：5432、6379。 文件与产物：数据目录 /home/user/data。 流式：不需要。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。apt 钉 postgresql 与 redis-server。用 pg_ctl 和 redis-server 以 user 启动。不要用需要 systemd 的脚本。实测 sudo 不能 mount，所以不要尝试把数据目录做成独立挂载。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU，2GB。 SDK：`Sandbox.create` 之后调用命名命令（`services_start`, `services_stop`）。依赖模板：无。

**需要。** 无密钥。无 Docker。

**极速版。** `yes`。限制因素：非 root 初始化数据库本次没跑，apt 通道已通。 能跑的子集：单机 Postgres + Redis。 其余：Runloop 的 DinD 在这里不可用（无 docker socket，mount 被拒绝）。

**上游与调用。** Debian 包。 无头形态：pg_isready 与 redis-cli ping。

**结论。** 状态 new，批次 1，优先级 P1，issue 本次新建。Express 上唯一可行的数据库形态。 来源：runloop:universal-dnd, modal:sandbox。

## ocr

**目的与用户。** 从图片里读文字。

**能力。** `ocr(image_path) -> {text}`。 端口：9000。 文件与产物：图片入、文本出。 流式：不需要。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。apt 钉 tesseract-ocr 与 tesseract-ocr-eng。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：1–2 vCPU。 SDK：`Sandbox.create` 之后调用命名命令（`ocr`）。依赖模板：无。

**需要。** 无。

**极速版。** `yes`。限制因素：无。 能跑的子集：整份。 其余：不需要。

**上游与调用。** Tesseract Apache-2.0。 无头形态：tesseract <img> stdout。

**结论。** 状态 new，批次 1，优先级 P2，issue 本次新建。小、可复现。 来源：upstream:tesseract。

## media-tools

**目的与用户。** CPU 转码。

**能力。** `transcode(args: list[str]) -> {stdout, stderr, exit_code}`，参数是列表。 端口：9000。 文件与产物：媒体文件。 流式：进度可选。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。apt 钉 ffmpeg，不要 CUDA。把包许可证写进 README。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU。 SDK：`Sandbox.create` 之后调用命名命令（`transcode`）。依赖模板：无。

**需要。** 无 GPU。

**极速版。** `yes`。限制因素：无。 能跑的子集：CPU 编解码。 其余：不需要。

**上游与调用。** Debian ffmpeg。E2B desktop 也装了 ffmpeg。 无头形态：ffmpeg -i in -c:v libx264 out。

**结论。** 状态 new，批次 1，优先级 P2，issue 本次新建。媒体 agent 的基础工具。 来源：e2b:desktop。

## tau2-bench

**目的与用户。** 工具调用评测，任务是模拟域，不是活网站。

**能力。** `tau2_run(domain) -> {score, log_path}`。模块路径从 tag v1.0.1 README 抄。 端口：9000。 文件与产物：评测日志。 流式：不强制。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。钉 https://github.com/sierra-research/tau2-bench tag v1.0.1（MIT，2026-07-22）。PyPI 名对不上就用 git tag。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU，2GB。 SDK：`Sandbox.create` 之后调用命名命令（`tau2_run`）。依赖模板：无。

**需要。** 模型 key，用户模拟器往往再要一次调用。

**极速版。** `yes`。限制因素：无 VM。 能跑的子集：一个 domain 的官方 runner。 其余：不需要。

**上游与调用。** sierra-research/tau2-bench v1.0.1 无头形态：该 tag 的 runner。

**结论。** 状态 new，批次 1，优先级 P1，issue 本次新建。不需要 Docker 的评测，适合极速版。 来源：upstream:tau2-bench。

## apply-patch

**目的与用户。** 让沙箱看懂 Codex 的 `*** Begin Patch` 方言。OpenSandbox 的 `/files/replace` 只做字面替换。

**能力。** `apply_patch(patch_text) -> {stdout, stderr, exit_code}`。补丁写到文件再喂给二进制，不要拼进 shell。 端口：9000。 文件与产物：被修改的工作区。失败可能留下半截改动。 流式：不需要。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。OpenSandbox 文档从 openai/codex 的某个 commit 编译 `codex-apply-patch`。文档里的 CODEX_REF 是占位符。先选定一个 commit 再写进 Dockerfile。基础镜像用平台镜像，不要 FROM opensandbox/execd。rust 构建很重，可以在构建阶段完成，运行镜像只留二进制。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：构建要更多内存；运行 2 vCPU 足够。 SDK：`Sandbox.create` 之后调用命名命令（`apply_patch`）。依赖模板：无。

**需要。** 无密钥。

**极速版。** `partial`。限制因素：可复现的 commit 还没选定，所以是 partial。 能跑的子集：选定 commit 之后，二进制本身不需要 Docker 或 KVM。 其余：不需要。

**上游与调用。** https://open-sandbox.ai/examples/apply-patch （2026-10-15 抓取）。examples/ 目录里没有这个文件夹，只有文档页。 无头形态：apply_patch < /tmp/change.patch。

**结论。** 状态 new，批次 2，优先级 P1，issue 本次新建。这是文件工具，不是又一个编码 CLI。 来源：opensandbox:apply-patch。

## osworld

**目的与用户。** OSWorld 那种看屏幕、点鼠标的计算机使用。用户是 GUI agent。

**能力。** `desktop_start() -> {display}`，`screenshot() -> png bytes`，`click(x,y)`，`type(text)`，`hotkey(keys)`，`a11y_tree() -> json`（若装了 at-spi，否则返回 unverified 空），`run_task_config(path)`，`evaluate(path) -> {score}`。 端口：noVNC 6080，可选。 文件与产物：PNG 截图、任务 json。 流式：VNC 是流；截图命令返回字节。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。apt 钉 xvfb、xdotool、scrot、openbox、x11vnc、novnc、websockify。不要写 ENTRYPOINT。命名命令启动 `Xvfb :99 -screen 0 1280x720x24` 和 openbox。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU，2GB。 SDK：`Sandbox.create` 之后调用命名命令（`desktop_start`, `screenshot`, `click`, `type`, `hotkey`, `evaluate`）。依赖模板：无。

**需要。** 无 KVM、无 GPU、无 Docker。虚拟显示即可。

**极速版。** `partial`。限制因素：完整 OSWorld 客户机是一台 VM，任务经常依赖特定 Ubuntu 应用快照。极速版没有 KVM。 能跑的子集：已实测：在 template base 里 apt 安装后，Xvfb :99、xdotool、scrot 写出 /tmp/s.png。openbox 已安装但没启动。所以截图/点击/打字这条 API 可以做。只移植不依赖 VM 快照的 evaluator 纯函数。不要承诺 OSWorld 排行榜分数。 其余：完整 VM 任务用 E2B desktop 或 Cube ubuntu-desktop（MicroVM）。OpenSandbox desktop 也是容器里的 Xvfb，和这个切片同类。

**上游与调用。** https://github.com/xlang-ai/OSWorld Apache-2.0。E2B surf 是桌面 agent 示例。 无头形态：screenshot + click + type。

**结论。** 状态 new，批次 2，优先级 P0，issue #36。issue #36 已覆盖，不新建 linux-desktop issue。探针证明切片不是空话。 来源：opensandbox:desktop, e2b:desktop, e2b-dev/surf, cube:ubuntu-desktop, cookbook:anthropic-computer-use-orangehrm-js。

## chrome

**目的与用户。** 同时给出 DevTools 和 VNC 的 Chrome，方便人看着 agent 点。

**能力。** `chrome_start() -> {cdp:9222, vnc:6080}`。 端口：9222、6080。 文件与产物：用户数据目录。 流式：VNC 与 CDP。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。在 osworld 的 Xvfb 上装钉死版本的 chromium，`--remote-debugging-port=9222 --disable-dev-shm-usage`。OpenSandbox 镜像名 opensandbox/chrome:latest 未钉，不要 FROM。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU，2GB。 SDK：`Sandbox.create` 之后调用命名命令（`chrome_start`）。依赖模板：osworld, browser-automation。

**需要。** 显示由 Xvfb 提供。shm 64M 已实测。

**极速版。** `partial`。限制因素：本次没在极速版安装 Chromium，只有 Xvfb。Chrome 能否在 2GB 和 64M shm 下稳定，unverified。 能跑的子集：先只做无头 CDP（并入 browser-automation）。VNC 叠在 osworld 上作为第二步。 其余：Cube sandbox-browser 在 MicroVM 里起 CDP，内存更大。

**上游与调用。** OpenSandbox examples/chrome。 无头形态：chromium --headless=new --remote-debugging-port=9222。

**结论。** 状态 new，批次 2，优先级 P1，issue 本次新建。和 Playwright 模板的差别是调试端口加可选画面。 来源：opensandbox:chrome, cube:browser-sandbox。

## swe

**目的与用户。** 在一个仓库的 base commit 上打补丁并跑 FAIL_TO_PASS。

**能力。** `swe_prepare(instance_id) -> {workdir}`，`swe_run_agent(instance_id, prompt) -> {patch}`，`swe_evaluate(instance_id) -> {fail_to_pass, pass_to_pass}`，`swe_report() -> json`。agent 用 mini-swe-agent，不单独再做模板。 端口：9000。 文件与产物：repo checkout、patch、测试日志。 流式：测试输出要流式。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。`pip install mini-swe-agent==2.4.6`。SWE-bench harness 只取数据集和测试命令，不要启动它的 Docker 后端。每个实例一个 venv：用数据集里的 python 版本若基础镜像没有，就只支持 3.13，并在报告里标明跳过。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU，2GB，磁盘是硬限制。 SDK：`Sandbox.create` 之后调用命名命令（`swe_prepare`, `swe_run_agent`, `swe_evaluate`, `swe_report`）。依赖模板：polyglot-toolchain。

**需要。** 模型 key。git。无 Docker。

**极速版。** `partial`。限制因素：官方评测为每个实例拉一个 Docker 镜像。极速版没有 docker，sudo 也不能 mount。 能跑的子集：一个实例：checkout base、打 patch、在 venv 里跑该实例声明的测试命令。不支持依赖系统包或 Docker 的实例。SWE-rebench 同样要预构建镜像，不能跑。 其余：完整分数用 E2B（e2b-dev/swe-bench）或 Cube mini-rl-training 那种带 Docker/MicroVM 的环境。

**上游与调用。** SWE-bench v5.0.1 MIT；mini-swe-agent v2.4.6 MIT；SWE-rebench/SWE-bench-fork。 无头形态：mini-swe-agent 本地后端 + pytest。

**结论。** 状态 new，批次 2，优先级 P0，issue #35。issue #35 已写明这个切片。 来源：cube:mini-rl-training, e2b-dev/swe-bench, upstream:SWE-bench, upstream:mini-swe-agent。

## polyglot-toolchain

**目的与用户。** 基础镜像没有的编译器。

**能力。** `toolchain_versions() -> {go, rustc, java}`。 端口：9000。 文件与产物：无。 流式：不需要。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。各一个 tarball：Go 1.25.x、一个钉死的 rustup toolchain、Temurin 21。不要多版本切换。构建后 df，超过约 8G 已用就砍掉 Rust。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU。磁盘是限制。 SDK：`Sandbox.create` 之后调用命名命令（`toolchain_versions`）。依赖模板：无。

**需要。** 无密钥。

**极速版。** `partial`。限制因素：10G rootfs，探针时空盘可用 9.3G，三个工具链加在一起 unverified。 能跑的子集：先装 Go 和 Temurin 21。 其余：OpenSandbox code-interpreter 预装了多版本，那是他们的镜像。

**上游与调用。** 官方 tarball。 无头形态：go version && java -version。

**结论。** 状态 new，批次 2，优先级 P1，issue 本次新建。编码 CLI 遇到 Go/Java 仓库会失败。 来源：opensandbox:sandbox-images。

## cursor-agent

**目的与用户。** Cursor 的 `agent` CLI，SWE-rebench 和 Fly Sprites 都在用。

**能力。** `agent(prompt) -> {stdout, stderr, exit_code}`。 端口：9000。 文件与产物：diff。 流式：`--output-format stream-json`。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。文档安装是 `curl https://cursor.com/install -fsS | bash`，不钉版本。找到带校验和的 URL 之前不要合并目录。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU，2GB。 SDK：`Sandbox.create` 之后调用命名命令（`agent`）。依赖模板：无。

**需要。** CURSOR_API_KEY。

**极速版。** `partial`。限制因素：安装不可复现。 能跑的子集：命令形状 `agent -p` 已在 https://cursor.com/docs/cli/headless 写明。二进制能否在 Debian 13 运行，unverified。 其余：E2B `cursor-agents` 是企业自建机器的调度器，不是这条 CLI。

**上游与调用。** https://cursor.com/docs/cli/headless 无头形态：agent -p "<prompt>"。

**结论。** 状态 new，批次 2，优先级 P1，issue 本次新建。需求真实，安装不达标。 来源：cursor-docs, fly-sprites-secondary, e2b:cursor-agents。

## grok

**目的与用户。** xAI 编码 CLI。

**能力。** `grok(prompt) -> {stdout, stderr, exit_code}`。 端口：9000。 文件与产物：diff。 流式：不强制。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。已知安装是 `curl -fsSL https://x.ai/cli/install.sh | bash`，无版本。xai-org/grok 不是 CLI。钉住二进制之前不要建目录。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU，2GB。 SDK：`Sandbox.create` 之后调用命名命令（`grok`）。依赖模板：无。

**需要。** XAI_API_KEY。本环境没有。无 GPU。

**极速版。** `partial`。限制因素：安装不可复现。 能跑的子集：命令 `grok --always-approve -p` 来自 E2B 文档。运行时不需要 KVM。 其余：E2B 别名 `grok` 已经预装。

**上游与调用。** https://docs.e2b.dev/agents/grok.md 无头形态：grok --always-approve -p "<prompt>"。

**结论。** 状态 new，批次 2，优先级 P1，issue #40。issue #40 已存在。 来源：e2b:grok。

## copilot-cli

**目的与用户。** GitHub Copilot 终端 agent。

**能力。** `copilot(prompt) -> {stdout, stderr, exit_code}`。 端口：9000。 文件与产物：diff。 流式：unverified。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。2026-10-15 GitHub 最新 release 是预发布 v1.0.99-0，许可证 SPDX NOASSERTION。无头 flag 只在二手页面出现（`copilot -p`、`--allow-all-tools`），未在上游文档核实。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU。 SDK：`Sandbox.create` 之后调用命名命令（`copilot`）。依赖模板：无。

**需要。** Copilot token，变量名 unverified。

**极速版。** `partial`。限制因素：没有稳定 pin，也没有核实过的 argv。 能跑的子集：等非预发布资产。 其余：OpenSandbox 有 github-copilot-cli-sandbox 示例。

**上游与调用。** https://github.com/github/copilot-cli 无头形态：unverified。

**结论。** 状态 new，批次 2，优先级 P1，issue 本次新建。示例存在，安装不达标。 来源：opensandbox:github-copilot-cli-sandbox。

## crush

**目的与用户。** Charm 的终端编码 agent。

**能力。** `crush(prompt)`。 端口：9000。 文件与产物：diff。 流式：unverified。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。可见 release 只有 nightly。npm `@charmland/crush` 与 `crush --yolo` 来自二手页面，unverified。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU。 SDK：`Sandbox.create` 之后调用命名命令（`crush`）。依赖模板：无。

**需要。** 模型 key。

**极速版。** `partial`。限制因素：无稳定 pin。 能跑的子集：有稳定 tag 之后就是一条普通 CLI，不需要 Docker。 其余：不需要。

**上游与调用。** https://github.com/charmbracelet/crush 无头形态：unverified。

**结论。** 状态 new，批次 2，优先级 P1，issue 本次新建。仓库活跃，安装不够格。 来源：upstream:charmbracelet/crush。

## cline

**目的与用户。** Cline 的 CLI 形态，不是 VS Code 扩展。

**能力。** `cline(prompt)`。 端口：9000。 文件与产物：diff。 流式：unverified。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。release v4.1.24（2026-10-13，Apache-2.0）。npm 包名和 `--yolo` 未在该 tag 核实。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU。 SDK：`Sandbox.create` 之后调用命名命令（`cline`）。依赖模板：无。

**需要。** 模型 key。

**极速版。** `partial`。限制因素：argv unverified。 能跑的子集：读完 tag 之后若是单二进制，就进极速版。 其余：不需要。

**上游与调用。** https://github.com/cline/cline v4.1.24 无头形态：unverified。

**结论。** 状态 new，批次 2，优先级 P1，issue 本次新建。70k stars，CLI 入口还没读到。 来源：upstream:cline/cline。

## deepagents

**目的与用户。** LangChain Deep Agents 的文件和 shell 工具跑在沙箱里面。

**能力。** `deepagents(task) -> {stdout}`。0.7.25 是否自带控制台脚本 unverified。没有的话用短 Python 驱动，工具只打本地文件系统。 端口：9000。 文件与产物：工作区。 流式：可选。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。`pip install deepagents==0.7.25`（2026-10-14，MIT）。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU，2GB。 SDK：`Sandbox.create` 之后调用命名命令（`deepagents`）。依赖模板：无。

**需要。** 模型 key。

**极速版。** `partial`。限制因素：入口 unverified。 能跑的子集：进程内 agent，不要再去创建 E2B/OpenSandbox。 其余：OpenSandbox 示例是宿主进程加他们的后端。E2B 没有公开别名。

**上游与调用。** https://github.com/langchain-ai/deepagents deepagents==0.7.25 无头形态：unverified。

**结论。** 状态 new，批次 2，优先级 P1，issue 本次新建。两边都有集成文档。 来源：opensandbox:deep-agents, e2b:agents/deep-agents。

## stagehand

**目的与用户。** Browserbase 的 Node 浏览器 SDK。

**能力。** `stagehand(instruction) -> {result}`。 端口：9000。 文件与产物：截图。 流式：可选。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。release 名 stagehand-server-v3/v3.7.6（2026-08-28）。npm 版本未核对。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU。shm 64M。 SDK：`Sandbox.create` 之后调用命名命令（`stagehand`）。依赖模板：browser-automation。

**需要。** 模型 key，或 BROWSERBASE_API_KEY。

**极速版。** `partial`。限制因素：API 未钉，且和 browser-use 重叠。 能跑的子集：本地 Chromium。云浏览器不是这个模板。 其余：Browserbase 云。

**上游与调用。** https://github.com/browserbase/stagehand 无头形态：unverified。

**结论。** 状态 new，批次 2，优先级 P2，issue 本次新建。只有调用方坚持要 Node SDK 时再做。 来源：cookbook:mcp-browserbase-js。

## prime-agent

**目的与用户。** Prime Intellect 的长程 agent。

**能力。** `prime_agent(prompt)`。 端口：9000。 文件与产物：工作区，可能有 IPython 状态。 流式：不强制。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。可见 release 只有 nightly。不要用浮动安装脚本。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU。 SDK：`Sandbox.create` 之后调用命名命令（`prime_agent`）。依赖模板：无。

**需要。** ANTHROPIC_API_KEY。

**极速版。** `partial`。限制因素：无稳定 pin。IPython 额外依赖 unverified。 能跑的子集：E2B 文档的 `prime-agent -p` 不需要 KVM。 其余：E2B 别名 `prime`。

**上游与调用。** https://github.com/PrimeIntellect-ai/prime-agent；https://docs.e2b.dev/agents/prime.md 无头形态：prime-agent -p "<prompt>"。

**结论。** 状态 new，批次 2，优先级 P2，issue 本次新建。命令已知，发布通道不够。 来源：e2b:prime。

## appworld

**目的与用户。** 可控应用世界里的函数调用评测。

**能力。** `appworld_run(task) -> {score}`。 端口：9000。 文件与产物：任务日志。 流式：不强制。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。tag v0.1.3.post1（2026-02-17，Apache-2.0）。是否调用 Docker unverified。若 README 要求 Docker 就停。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU。 SDK：`Sandbox.create` 之后调用命名命令（`appworld_run`）。依赖模板：无。

**需要。** 模型 key。

**极速版。** `partial`。限制因素：Docker 依赖未核实。 能跑的子集：纯 Python 任务可以跑。 其余：若必须 Docker，用 Cube 或 E2B 的 Docker 配方，不是极速版。

**上游与调用。** https://github.com/stonybrooknlp/appworld 无头形态：该 tag 的 runner。

**结论。** 状态 new，批次 2，优先级 P2，issue 本次新建。比 tau2 旧，放后面。 来源：upstream:appworld。

## muse

**目的与用户。** Meta 的终端/CI 编码 agent。

**能力。** `muse(prompt)`。 端口：9000。 文件与产物：diff。 流式：`--json`。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。E2B 预装了它。公开安装 pin 本次没找到，GitHub 上没有 facebook/muse 或 meta-llama/muse。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU。 SDK：`Sandbox.create` 之后调用命名命令（`muse`）。依赖模板：无。

**需要。** META_API_KEY。

**极速版。** `partial`。限制因素：没有可复现安装物。 能跑的子集：`muse exec --yolo` 不需要 KVM，前提是二进制存在。 其余：E2B 别名 `muse`。cookbook muse-execution-backend 是宿主示例。

**上游与调用。** https://docs.e2b.dev/agents/muse.md；https://dev.meta.ai/docs/muse-code 无头形态：muse exec --yolo "<prompt>"。

**结论。** 状态 new，批次 2，优先级 P2，issue 本次新建。E2B 有，我们没有安装物。 来源：e2b:muse, cookbook:muse-execution-backend-python。

## devin

**目的与用户。** Cognition 的终端编码 agent。

**能力。** `devin(prompt)`，`devin --permission-mode dangerous -p`。 端口：9000。 文件与产物：diff。 流式：不强制。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。E2B 别名 `devin`。首次要交互登录。无头安装 pin unverified。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU。 SDK：`Sandbox.create` 之后调用命名命令（`devin`）。依赖模板：无。

**需要。** Devin 账号。

**极速版。** `partial`。限制因素：登录是交互的。 能跑的子集：若能用 token 跳过登录，命令本身不需要 KVM。未验证。 其余：E2B `devin` 与 `devin-outposts`（企业调度器）。

**上游与调用。** https://docs.e2b.dev/agents/devin.md 无头形态：devin --permission-mode dangerous -p "<prompt>"。

**结论。** 状态 new，批次 2，优先级 P2，issue 本次新建。登录挡住了可复现安装。 来源：e2b:devin, e2b:devin-outposts。

## waa

**目的与用户。** Windows 上的计算机使用评测。

**能力。** `rdp_open(host) -> {status}`，`winrm_run(command) -> {stdout}`。不在沙箱里跑 Windows。 端口：出站 3389/5985，不在沙箱内监听 Windows。 文件与产物：截图若远程桌面客户端能抓。 流式：不强制。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。安装钉死版本的 freerdp 客户端或 pywinrm。不要装 QEMU。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU。 SDK：`Sandbox.create` 之后调用命名命令（`winrm_run`）。依赖模板：无。

**需要。** 一台调用方提供的 Windows 目标。无 KVM 也变不出 Windows。

**极速版。** `partial`。限制因素：极速版是 Linux 容器。OpenSandbox 的 dockurr/windows 要 KVM/QEMU。探针没有 /dev/kvm，sudo mount 失败。 能跑的子集：作为远程 RDP/WinRM 客户端，连一台已经存在的 Windows。评测脚本里的 Windows 应用仍在那台机器上。 其余：Windows 客户机用 Cube MicroVM（他们的桌面示例是 Linux）、OpenSandbox windows 示例（dockurr/windows，要 KVM）、Daytona windows-* 快照、E2B 不提供 Windows。

**上游与调用。** https://github.com/microsoft/WindowsAgentArena v0.0.4 MIT。 无头形态：xfreerdp 或 WinRM。

**结论。** 状态 new，批次 3，优先级 P2，issue #37。issue #37。不要写裸的 no。 来源：opensandbox:windows, daytona:windows-snapshots, upstream:WAA。

## phone-sandbox

**目的与用户。** 一台手机或模拟器：屏幕和触摸。

**能力。** `adb_connect(addr) -> {serial}`，`adb_screencap() -> png`，`adb_input(cmd)`。 端口：出站 5555。 文件与产物：截图。 流式：scrcpy 可选，未验证。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。apt 钉 android-tools-adb 或官方 platform-tools 的版本化 zip。不要装模拟器系统镜像。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：客户端 2 vCPU 足够。 SDK：`Sandbox.create` 之后调用命名命令（`adb_connect`, `adb_screencap`, `adb_input`）。依赖模板：android-world。

**需要。** 调用方提供的设备或远程模拟器。沙箱 API 没有手机资源。

**极速版。** `partial`。限制因素：没有 /dev/kvm，也没有设备节点。 能跑的子集：adb 客户端连 `host:5555`。屏幕和触摸发生在远端。 其余：模拟器本身用带 KVM 的 OpenSandbox/Cube/E2B android-16（redroid）。

**上游与调用。** 没有单一上游。E2B android-16 是相邻能力。 无头形态：adb connect && adb exec-out screencap -p。

**结论。** 状态 new，批次 3，优先级 P2，issue #38。issue #38。 来源：e2b:android-16。

## android-world

**目的与用户。** 在 Android 模拟器里跑 116 个动态任务。

**能力。** `android_eval(task) -> {score}` 只有在 adb 已连上时才有意义。 端口：adb 5555，gRPC 8554 是模拟器侧。 文件与产物：任务日志。 流式：不强制。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。pip 钉 android_world 的某个 commit（仓库无 release）。不要下载 AVD 系统镜像。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：客户端 2 vCPU。模拟器要 KVM 和数 GB。 SDK：`Sandbox.create` 之后调用命名命令（`adb_connect`, `android_eval`）。依赖模板：phone-sandbox。

**需要。** 远端模拟器。无本地 GPU 需求。

**极速版。** `partial`。限制因素：官方启动是 `emulator -avd AndroidWorldAvd -grpc 8554`。探针无 /dev/kvm。 能跑的子集：把环境变量指到远程 adb。accessibility 转发若绑在本地 gRPC，则只有命令通道能用，任务复位 unverified。 其余：E2B `android-16` 在他们的 microVM 里跑 redroid。Cube/OpenSandbox 若给 KVM 也能跑模拟器。

**上游与调用。** https://github.com/google-research/android_world Apache-2.0。 无头形态：python run.py 指向远程 adb。

**结论。** 状态 new，批次 3，优先级 P2，issue #39。issue #39。 来源：e2b:android-16, upstream:android_world。

## k3s

**目的与用户。** 一次性 Kubernetes。E2B `e2b/k3s` 是单节点集群。

**能力。** `kubectl_apply(manifest) -> {stdout}`，kubeconfig 由调用方传入。 端口：出站 6443。 文件与产物：kubeconfig 只从环境变量读，不写进镜像。 流式：不需要。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。安装钉死版本的 kubectl 静态二进制。不要装 k3s、containerd 或 CNI。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：客户端可忽略。 SDK：`Sandbox.create` 之后调用命名命令（`kubectl_apply`）。依赖模板：无。

**需要。** 一台外部 apiserver。

**极速版。** `partial`。限制因素：探针：无 docker socket，sudo mount 失败，无 fuse。k3s 要 cgroup 和容器运行时。E2B 能跑是因为 microVM，且他们自己的文档也写了没有 BPF JIT、不能 Kata/KubeVirt。 能跑的子集：kubectl 客户端。集群不在这个沙箱里。 其余：真集群用 E2B `e2b/k3s`，或 OpenSandbox 的 AKS+Kata / kubernetes-sigs agent-sandbox。Cube 也是 MicroVM，不是在容器里套 k3s。

**上游与调用。** https://docs.e2b.dev/use-cases/k3s.md 无头形态：kubectl get nodes。

**结论。** 状态 new，批次 3，优先级 P2，issue #42。issue #42。 来源：e2b:e2b/k3s, opensandbox:agent-sandbox, opensandbox:aks-kata。

## omarchy

**目的与用户。** basecamp/omarchy 是一套 Arch + Hyprland 桌面意见。它不是编码 CLI。

**能力。** 没有提示词命令。不要发明一个。若只是想要主题字体，那不是这个模板的目的。 端口：无。 文件与产物：无。 流式：无。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。不要在 Debian 13 上安装 Arch/Hyprland。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：不适用。 SDK：`Sandbox.create` 之后调用命名命令（（无））。依赖模板：osworld。

**需要。** 真实座位和 Wayland。Xvfb 不能满足 Hyprland。

**极速版。** `partial`。限制因素：发行版和显示栈都不是极速版。 能跑的子集：没有任何 Hyprland 会话可跑。要桌面用 `osworld` 的 Xvfb+openbox。Omarchy 的 CLI 工具若将来单独发布，再单独立项。 其余：一台 Arch 虚拟机（Cube/E2B 自定义镜像），不是 Express。

**上游与调用。** https://github.com/basecamp/omarchy v4.0.4 MIT。 无头形态：无。

**结论。** 状态 new，批次 3，优先级 P2，issue #43。issue #43。切片是承认它没有无头入口，并把桌面需求指到 osworld。 来源：upstream:omarchy。

## qm

**目的与用户。** yc-software/qm 是带可插拔沙箱后端的 agent harness。

**能力。** `qm_run(task) -> {stdout}` 仅当存在不外出的 local shell 后端。 端口：9000。 文件与产物：qm 工作区。 流式：unverified。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。钉 tag desktop-v0.1.2 只是预发布。先读该 tag 是否有 local 后端。不要把 Docker/E2B/Modal 后端编进镜像。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：2 vCPU。 SDK：`Sandbox.create` 之后调用命名命令（`qm_run`）。依赖模板：无。

**需要。** 模型 key。后端租约不在我们的 server 里。

**极速版。** `partial`。限制因素：产品价值在后端路由。极速版提供不了那些后端。 能跑的子集：若代码能把 shell 打到本容器，就只暴露这一条。远程后端不做。本次未读源码确认 local 后端，标 unverified。 其余：E2B、Modal、MicroVM 后端由那些平台自己提供。

**上游与调用。** https://github.com/yc-software/qm MIT。 无头形态：unverified。

**结论。** 状态 new，批次 3，优先级 P2，issue #44。issue #44。 来源：upstream:qm。

## qm-sandbox

**目的与用户。** QM 的沙箱层。文档里的一种接法是 Superserve 模板 `qm-agent-0.1.0`。

**能力。** 不在极速版注册 Superserve 模板。最多 `qm_sandbox_status()` 打印“需要外部后端”。 端口：无。 文件与产物：无。 流式：无。

**构建。** `FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。不要 COPY 后端控制面。 平台 generation 2 的 start_cmd 固定为 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，ready_cmd 为 `agent-sandbox-server healthcheck --port 9000`。不要写镜像 CMD/ENTRYPOINT。资源：无。 SDK：`Sandbox.create` 之后调用命名命令（（无））。依赖模板：qm。

**需要。** SUPERSERVE_API_KEY 与外部模板。

**极速版。** `partial`。限制因素：`abx template install` 不会创建 `qm-agent-0.1.0`。 能跑的子集：没有可执行的沙箱实现。调用方应直接使用本目录里的 CLI 模板，而不是绕到 QM。 其余：Superserve、E2B、Modal、Cube MicroVM。

**上游与调用。** QM 文档中的 SUPERSERVE_TEMPLATE。 无头形态：无。

**结论。** 状态 new，批次 3，优先级 P2，issue #45。issue #45。 来源：upstream:qm-sandbox。
