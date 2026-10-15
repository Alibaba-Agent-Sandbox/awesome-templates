# 模板市场调研（2026-10）

## English summary

Survey date: 2026-10-15. Catalog baseline: `awesome-templates` `main` at `8acab57` (Gemini CLI template). This document decides which **new** Agent Sandbox templates to build for Alibaba Cloud Express (2 vCPU, non-root `user`, no KVM, no Docker, no capabilities, egress works, FC base image has Python 3.13 and Node 20, rootfs about 10G). Platform entrypoint cannot be replaced.

E2B's public aliases (from docs fetched this date, not from the templates API) already cover `base`, `code-interpreter-v1`, `desktop`, `claude`, `codex`, `amp`, `opencode`, `openclaw`, `droid`, `grok`, `pi`, `hermes`, `devin`, `muse`, `prime`, `kernel-browser`, `e2b/k3s`, `android-16`, `cursor-agents`, `devin-outposts`, and `E2B/claude-managed-agents-webhooks`. OpenSandbox publishes a pinned `code-interpreter:v1.1.0` and example images for desktop, Playwright, VS Code, Chrome, and an all-in-one sandbox. CubeSandbox publishes `sandbox-code` and `sandbox-browser`. Daytona, Vercel, Cloudflare, Runloop, and Fly Sprites ship fat base images with coding CLIs preinstalled rather than one template per agent. Modal sells image-builder snapshots, not a public agent catalog. Morph's public snapshot catalog was not verified.

Do not rebuild templates that already exist: `python-hello`, `browser-automation`, `claude-code`, `codex`, `codex-agent-api`, `qoder`, `agents-cli`, `qwen-code`, `deepseek-harness`, `hermes-agent`, `node-web`, `openclaw`, `opencode`, `amp`, `droid`, `gemini`. Upgrade `hermes-agent` (it does not install the Hermes CLI) and keep `gemini` experimental until a keyed e2e exists.

Build next, P0: `kimi-code`, `goose`, `pi`, `browser-use`, `code-interpreter` (slim), `linux-desktop` (Xvfb, not OSWorld). P1 includes `cursor-agent` and `grok` only after a versioned install exists. Full SWE-bench, OSWorld, Windows Agent Arena, phone sandbox, AndroidWorld, K3s, Omarchy, qm, and qm-sandbox do not fit Express. Machine-readable list: `docs/template-backlog.json`.

Items marked **unverified** were not confirmed against an upstream file or API response in this pass.

## 范围和方法

日期：2026-10-15。

读过的材料：

- 本仓库 `main` 的 `awesome-templates.yaml`、`registry/catalog.json`、`docs/backlog.md`、`docs/acceptance.md`。
- E2B 文档索引 [https://docs.e2b.dev/llms.txt](https://docs.e2b.dev/llms.txt) 以及下面各节列出的 markdown 页面。没有 E2B API key，没有调用 `GET /v2/templates`。公开别名清单来自文档，可能漏掉未写入文档的公开模板。
- GitHub API（2026-10-15）：`e2b-dev` 组织仓库、`alibaba/OpenSandbox` 的 `examples/`、`opensandbox-group/sandbox-images`、`tencentcloud/CubeSandbox` 的 `examples/`，以及候选上游的 star、license SPDX、`pushed_at` 和最新 release。
- 厂商文档页面，链接写在各节。

没有做的事：没有打开 GitHub Trending 网页。近三个月活跃度用的是 API 的 `pushed_at >= 2026-07-15`，star 数是累计值，不是三个月内的新增。没有在 Express 上实际安装这些 CLI。

Express 约束（本程序 2026-10-15 已核实，写进实施说明）：非 root 用户 `user`，2 vCPU，没有 `/dev/kvm`，没有 Docker，没有 capabilities，出网可用，平台基础镜像是 `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`（当前 tag `v0.0.49`），不能写 `CMD` / `ENTRYPOINT`。`docs/acceptance.md` 仍写着 `FROM python:3.12-slim`。那条和现行平台契约不一致。新模板按平台基础镜像写，不要照 acceptance 里的旧 Dockerfile 句子。

`docs/acceptance.md` 还写明：OpenSandbox 已发布的 `code-interpreter`、`code-interpreter-base`、`desktop`、`playwright`、`vscode` 由 SDK 把短名字解析成镜像，不要把那些 Dockerfile 拷进本仓库。下面建议的同名能力是给极速版用的新镜像，`FROM` 平台基础镜像，自己钉包版本，不是把 OpenSandbox 的 Dockerfile 搬过来。

## 已经在目录里的，不要再建

| name | 状态 | 备注 |
|---|---|---|
| python-hello | official | 最小 Python |
| browser-automation | official | Playwright + Chromium |
| claude-code | official | |
| codex | official | |
| codex-agent-api | official | Codex CLI 上的 Agents API |
| qoder | official | 描述写明没有安装 Qoder CLI |
| agents-cli | official | 镜像里没有预装 Codex 或 Qwen |
| qwen-code | official | |
| deepseek-harness | official | |
| hermes-agent | official | 描述写明只做聊天补全，不注册工具 |
| node-web | official | Express/Fastify 类服务，不是 Next/Vite 脚手架 |
| openclaw | official | |
| opencode | experimental | `opencode-ai@1.19.0`，命令 `opencode run` |
| amp | experimental | |
| droid | experimental | `@factory/cli@0.241.1`，命令 `droid exec` |
| gemini | experimental | `@google/gemini-cli@0.64.0`，命令 `gemini -p`，还没有带密钥且输出含 `ABX_E2E_OK` 的记录 |

## 1. E2B

文档入口：[Templates](https://docs.e2b.dev/template/quickstart.md)、[Base image](https://docs.e2b.dev/template/base-image.md)、[Coding agents](https://docs.e2b.dev/use-cases/coding-agents.md)。组织仓库 [e2b-dev](https://github.com/e2b-dev) 在 2026-10-15 有 85 个公开仓库。和模板市场直接相关的是 `E2B`（14,355 stars，Apache-2.0）、`code-interpreter`（2,418，Apache-2.0）、`desktop`（1,531，Apache-2.0）、`fragments`（6,389，Apache-2.0）、`surf`（873，Apache-2.0）、`open-computer-use`（2,360，许可证未在本次 API 输出里单列）、`awesome-ai-agents`（30,445，一份清单，不是沙箱镜像）。

`fragments` 是生成式应用的 Next.js 模板，不是预置沙箱。`surf` 和 `open-computer-use` 是跑在 Desktop 沙箱上的计算机使用示例。`e2b-dev/swe-bench`（5 stars，2026-09-08 更新）和 `e2b-dev/osworld-e2b`（1 star，2026-09-16）是评测移植，不是公开别名。

默认 `base`：不传 template 时使用。Debian，预装 Python 3、Node.js、Yarn、git、curl、build-essential、GitHub CLI `gh`。Dockerfile：[templates/base/e2b.Dockerfile](https://github.com/e2b-dev/E2B/blob/main/templates/base/e2b.Dockerfile)。构建基础镜像名 `e2bdev/base`。默认 2 vCPU、512 MiB。NixOS 要用 `e2bdev/nixos`，那是构建用基础镜像，不是下面表格里的沙箱别名。

下表「公开别名」指文档里出现 `e2b sbx create <name>` 或 `Sandbox.create("<name>")`。抓取日期 2026-10-15。

| 别名 | 用途 | 里面有什么 | 无头调用 |
|---|---|---|---|
| `base` | 默认 Linux 沙箱 | 见上 | `commands.run` |
| `code-interpreter-v1` | Code Interpreter SDK | Python、JS/TS、R、Java、Bash。服务端口 49999。Python 依赖见仓库 `template/requirements.txt`（2026-10-15 从 main 拉取）：jupyter-server 2.20.0、pandas 2.2.3、numpy 2.3.5、matplotlib 3.10.9、scikit-learn 1.6.1、spacy 3.8.14、opencv-python 4.11.0.86 等 | SDK `run_code`，不是一条 agent CLI |
| `desktop` | 计算机使用 | Ubuntu 22.04、XFCE、noVNC 6080、LibreOffice、xdotool、scrot、ffmpeg、x11vnc。Desktop SDK 默认模板。分辨率默认 1024×768 | `screenshot()`、鼠标键盘 API、`stream.start()` |
| `claude` | Claude Code | 预装 Claude Code | `claude --dangerously-skip-permissions -p "..."`，密钥 `ANTHROPIC_API_KEY` |
| `codex` | Codex CLI | 预装 Codex | `codex exec --full-auto`，密钥 `CODEX_API_KEY` |
| `amp` | Amp | 预装 Amp | `amp --dangerously-allow-all -x "..."`，密钥 `AMP_API_KEY` |
| `opencode` | OpenCode | 预装 OpenCode | `opencode run "..."`；另有 `opencode serve --port 4096` |
| `openclaw` | OpenClaw gateway | 文档用 `Sandbox.create("openclaw")`，页面正文没有写 pre-built 这三个词，但是公开别名 | `openclaw gateway --allow-unconfigured --bind lan --port 18789`，不是单次提示词 |
| `droid` | Factory Droid | 预装 Droid | `droid exec --auto low "..."`，密钥 `FACTORY_API_KEY` |
| `grok` | xAI Grok Build | 预装 Grok Build | `grok --always-approve -p "..."`，密钥 `XAI_API_KEY` |
| `pi` | Pi | 预装 Pi | 文档写 `pi -p "..."`，密钥 `ANTHROPIC_API_KEY` |
| `hermes` | Hermes Agent | Hermes CLI 和自带 skills | `hermes chat -Q --yolo --provider ... -q "..."` |
| `devin` | Devin for Terminal | 预装 Devin | `devin --permission-mode dangerous -p "..."`。首次要交互登录 |
| `muse` | Meta Muse Code | 预装 Muse Code。[上游文档](https://dev.meta.ai/docs/muse-code) | `muse exec --yolo "..."`，密钥 `META_API_KEY` |
| `prime` | Prime Agent | 预装，命令 `prime-agent`。[仓库](https://github.com/PrimeIntellect-ai/prime-agent) | `prime-agent -p "..."` |
| `kernel-browser` | 云浏览器 | Kernel SDK、Playwright、Browser Use | 需要 `KERNEL_API_KEY`。浏览器在 Kernel，不在沙箱里 |
| `e2b/k3s` | 单节点 k3s | kubectl、Flannel VXLAN、Traefik、local-path | `kubectl get nodes`。限制：无 BPF JIT，无 Kata/KubeVirt，无多节点 |
| `android-16` | Android 16 | redroid，构建期启动，adb `127.0.0.1:5555` | `adb shell`、`screencap` |
| `cursor-agents` | Cursor 自建机器调度器 | 为每个请求再起 `cursor-agents-worker` | 需要 Cursor Enterprise 和 service-account key。不是 `agent -p` |
| `devin-outposts` | Devin Outposts 调度器 | worker 模板 `devin-outposts-worker` | 需要 Devin Enterprise，`cog_` token |
| `E2B/claude-managed-agents-webhooks` | Claude Managed Agents 的 webhook | 端口 8000 | 需要 Anthropic environment id 和 key |

文档里的 Docker、Next.js、Expo 示例是让用户自己 `Template.build` 的配方，构建名可以叫 `docker`，不是上表这种公开别名。

E2B 沙箱没有 GPU（[FAQ](https://docs.e2b.dev/faq/gpu-support.md)）。k3s 和 Android 能跑，是因为沙箱是 microVM，有自己的内核；这不能照搬到极速版容器。

## 2. OpenSandbox

仓库 [alibaba/OpenSandbox](https://github.com/alibaba/OpenSandbox)（与 `opensandbox-group/OpenSandbox` 同一仓库，15,858 stars，2026-10-14 更新）。示例头注释写 Apache-2.0。示例索引：[docs/examples/index.md](https://github.com/alibaba/OpenSandbox/blob/main/docs/examples/index.md)，目录以 2026-10-15 的 `examples/` 列表为准。

镜像仓库 [opensandbox-group/sandbox-images](https://github.com/opensandbox-group/sandbox-images)（2 stars）目前只构建并发布 `code-interpreter` 和 `code-interpreter-base`。README 写明基于 Ubuntu 24.04，预装 Python 3.10–3.14（uv，3.14 为实验）、Java 8/11/17/21、Maven 3.9.2、Node 18/20/22、Go 1.23/1.24/1.25，以及 Jupyter 内核（ipykernel、IJava、tslab、gonb、bash_kernel）。默认版本 Python 3.14、Java 21、Node 22、Go 1.25。Jupyter 在 `127.0.0.1:44771`。amd64 带 clone3-workaround v1.0.0。示例代码里的钉扎引用是 `sandbox-registry.cn-zhangjiakou.cr.aliyuncs.com/opensandbox/code-interpreter:v1.1.0`，Docker Hub 名 `opensandbox/code-interpreter:v1.1.0`（文档页 [code-interpreter](https://open-sandbox.ai/examples/code-interpreter)）。

其它名字是示例 Dockerfile 或浮动 tag，不是这个镜像仓库的独立发布：

| 示例 | 镜像 | 做什么 |
|---|---|---|
| code-interpreter | `.../code-interpreter:v1.1.0` | Python/Java/TS/Go 代码执行 |
| desktop | `opensandbox/desktop:latest`（未钉） | Xvfb + XFCE + x11vnc + noVNC。密码 `VNC_PASSWORD` |
| playwright | `opensandbox/playwright:latest`（未钉） | 无头 Chromium 抓标题和截图 |
| vscode | `opensandbox/vscode:latest`（未钉） | code-server，端口默认 8443 |
| chrome | `opensandbox/chrome:latest` | VNC + DevTools |
| aio-sandbox | `ghcr.io/agent-infra/sandbox:latest`（未钉） | 别人的 all-in-one 镜像，接 OpenSandbox |
| windows | `dockurr/windows:latest`，`VERSION=11` | KVM/QEMU Windows 客户机 |
| claude-code、codex-cli、gemini-cli、opencode、qwen-code | 同上 code-interpreter:v1.1.0 | 启动后再 `npm i -g ...@latest`，未钉 CLI 版本 |
| kimi-cli | 同上 | 启动后 `pip install kimi-cli`（未钉）。这是旧的 Python CLI；现行产品是 Kimi Code |
| openclaw | `ghcr.io/openclaw/openclaw:latest`（未钉） | Gateway，端口 18789 |
| langgraph、deep-agents、deer-flow、google-adk、microsoft-agent-framework | 代码在宿主编排，工具进沙箱 | 不是一块预置镜像 |
| harbor-evaluation | 每个 trial 一个沙箱 | Harbor 评测 |
| agent-sandbox、aks-kata | Kubernetes / AKS Kata | 需要集群和 VM 隔离 |
| 各类 volume-mount | 挂载演示 | 不是应用模板 |

`examples/` 里还有 `client-pool-schedule`、`github-copilot-cli-sandbox`。索引页还列了 Apply Model Patches，本次目录列表里没有单独文件夹，以目录列表为准。

## 3. CubeSandbox

仓库 [tencentcloud/CubeSandbox](https://github.com/tencentcloud/CubeSandbox)（12,942 stars，2026-10-15 更新）。许可证 SPDX 本次没有单独拉取，记为 **unverified**。模板是 OCI 镜像加热启动的 MicroVM 快照，镜像本身不能直接当模板用。[模板说明](https://github.com/tencentcloud/CubeSandbox/blob/master/docs/guide/templates.md)。

已在文档里给出仓库地址的官方镜像：

| 镜像 | 用途 |
|---|---|
| `cube-sandbox-int.tencentcloudcr.com/cube-sandbox/sandbox-code:latest`（中国大陆用 `cube-sandbox-cn`） | 代码解释器。端口 49999 和 envd 49983。只有这个 tag 被写成多架构。`:latest` 未钉 |
| `.../sandbox-browser:latest` | Chromium remote debugging，端口 9000，Playwright 走 CDP |
| `ghcr.io/tencentcloud/cubesandbox-base:2026.16`（教程里也出现 `:latest`） | 带 envd 的基础镜像，端口 49983 |

Ubuntu 桌面不是预置镜像。`examples/ubuntu-desktop` 要自己构建：Ubuntu 22.04 GNOME，noVNC 6080，建议 4 vCPU / 8G。[指南](https://cubesandbox.com/guide/integrations/ubuntu-desktop)。

`examples/`（2026-10-15）：`code-sandbox-quickstart`、`browser-sandbox`、`cubesandbox-base-nginx`、`ubuntu-desktop`、`claude-code-integration`、`openclaw-integration`、`opencode-plugin-sandbox`、`pi-agent-integration`、`langchain-integration`、`openai-agents-example`、`openai-agents-code-interpreter`、`mcp-gateway`、`snapshot-rollback-clone`、`volume`、`host-mount`、`network-policy`、`route-aware-egress`、`grpc-ingress`、`ivshmem`、`mini-rl-training`、`cube-bench`、`e2b-dev-sidecar`、`run-code-env-inheritance`。这些是集成示例，除了上面三块镜像，没有另一套可直接 `tpl create-from-image` 的公开目录。Cube 需要 KVM。极速版对不上。

## 4. 其它沙箱产品里值得对齐的现成环境

### Daytona

[Snapshots](https://www.daytona.io/docs/en/snapshots/)（抓取 2026-10-15）的默认快照是规格，不是 agent 名：`daytona-small/medium/large`（容器）、`daytona-gpu`、`daytona-vm-*`、`windows-small/medium/large`。默认镜像 README（[daytonaio/daytona images/sandbox](https://github.com/daytonaio/daytona/blob/46f29d5b/images/sandbox/README.md)）写明预装 Python 数据栈（numpy、pandas、torch、transformers 等，版本表在快照文档里，例如 pydantic-ai v1.47.0）以及 `@anthropic-ai/claude-code`、`@openai/codex`、`openclaw`、`opencode-ai`。值得对齐的是「一块能写代码的数据镜像」加上已经有的编码 CLI，不是再做一个 Windows 或 GPU 快照。Windows 和 GPU 在 Express 上不可行。

### Modal

[Images](https://modal.com/docs/guide/images) 默认是 Debian slim，Python 小版本跟着本机走。没有公开的 agent 模板目录。文件系统快照和目录快照是产品能力。内存快照在 Runloop 迁移文档里被写成 Alpha，7 天过期，不能带 GPU。不作为本目录的下一批模板。

### Cloudflare Sandbox

两个页面版本号不一致，当前 tag **unverified**：

- [DOCKER_README.md](https://github.com/cloudflare/sandbox-sdk/blob/main/DOCKER_README.md) 写 `cloudflare/sandbox:0.12.7`，Ubuntu 22.04，Node 24、Bun、git、curl、jq；变体 `-<version>-python`（Python 3.11，matplotlib/numpy/pandas/ipython）、`-opencode`、`-musl`。
- [官方 Dockerfile 文档](https://developers.cloudflare.com/sandbox/sdk/configuration/dockerfile/) 的示例仍是 `0.7.0`，并写 Node 20。

对齐点：默认镜像里带 OpenCode 变体，以及一份小的 Python 数据栈。镜像 tag 必须和 `@cloudflare/sandbox` 的 npm 版本一起钉，不能抄上面任一页的数字当永恒版本。

### Vercel Sandbox

[更新说明](https://vercel.com/changelog/vercel-sandbox-managed-images)（抓取 2026-10-15）：默认 `vercel/sandbox/universal:latest`，Ubuntu 26.04，Node 24，Python 3.14 + uv，预装 `opencode`、`claude-code`、`codex`、`pi`，以及 git、vim、nano、tmux、ripgrep、jq、fzf。另有 `node:22|24|26`、`python:3.14`、`ubuntu:latest`、`arch:latest`。`latest` 每晚滚动，不适合当本仓库的钉扎。值得抄的是组合：Pi 和三种编码 CLI 放进基础环境。本目录已经有后三种，缺 Pi。

### Runloop

[预置 blueprint](https://docs.runloop.ai/docs/devboxes/blueprints/overview)（抓取 2026-10-15）：`runloop/starter-x86_64` 与 arm64、`runloop/universal-ubuntu-22.04-*`、`universal-ubuntu-24.04-*`、带 Docker-in-Docker 的 `universal-*-dnd` 和 `ubuntu-dnd-*`。starter 是不指定镜像时的默认。没有按 agent 拆开的公开模板。DinD 在 Express 上不可用。对齐 starter/universal 的「常用开发工具」即可。

### Morph

本次没有找到一份可核对的 Morph 公开沙箱快照目录。Morph 作为代码编辑/MCP 层的二手描述，不能当成模板市场。记为 **unverified**，不建议为此建模板。

### Fly Sprites

二手对比页 [fly.io/learn/fly-vs-vercel](https://fly.io/learn/fly-vs-vercel/)（抓取 2026-10-15）写 Sprites 预装 Claude Code、Cursor CLI、Gemini CLI、Codex CLI，以及 Node、Python、Go、Ruby、Rust、Java、Elixir。这不是 Sprites 参考手册原文，预装列表记为二手。对齐点是 Cursor CLI 和多语言工具链。Sprites 的持久磁盘和内存挂起 Express 没有。

## 5. 近三个月仍在更新、适合做成沙箱模板的上游

门槛：GitHub `pushed_at` 在 2026-07-15 之后，并且是编码 CLI、agent 运行时、浏览器代理、评测套件或开发环境。star 为 2026-10-15 的累计值。

已经在目录里、只作升级候选的：OpenCode 213,544（MIT）、OpenClaw 392,032（MIT）、Gemini CLI 107,372（Apache-2.0）、Qwen Code 28,485（Apache-2.0）、Hermes Agent 253,814（MIT，release v0.22.1，2026-10-14）。Claude Code 与 Codex 仓库也在更新，目录里已有模板。

值得新做或已经写进 backlog 的，见第 8 节。明确不新做目录的活跃项目：

| 项目 | stars | 许可证 | 为什么不单开 |
|---|---|---|---|
| [basecamp/omarchy](https://github.com/basecamp/omarchy) v4.0.4 | 44,844 | MIT | Arch + Hyprland 桌面发行版，没有无头提示词命令 |
| [yc-software/qm](https://github.com/yc-software/qm) desktop-v0.1.2 预发布 | 15,417 | MIT | 沙箱后端路由器（Docker、MicroVM、E2B、Modal 等），不是一条 CLI |
| [Skyvern-AI/skyvern](https://github.com/Skyvern-AI/skyvern) v1.0.56 | 23,199 | AGPL-3.0 | 浏览器工作流，通常要自带浏览器栈；AGPL 不适合作为默认官方模板。browser-use 已覆盖同类需求 |
| [RooCodeInc/Roo-Code](https://github.com/RooCodeInc/Roo-Code) v3.54.0，pushed 2026-05-15 | 24,280 | Apache-2.0 | 编辑器插件，三个月内无推送。无头 CLI **unverified** |
| [Kilo-Org/kilocode](https://github.com/Kilo-Org/kilocode) v7.8.10 预发布 | 27,604 | MIT | 二手页面写 `kilo run --auto`，上游无头入口本次 **unverified** |
| [plandex-ai/plandex](https://github.com/plandex-ai/plandex) server/v2.2.1，2025-07 | 15,723 | MIT | 不在三个月窗口内 |
| [xlang-ai/OSWorld](https://github.com/xlang-ai/OSWorld) | 3,209 | Apache-2.0 | 要桌面虚拟机 |
| [SWE-bench/SWE-bench](https://github.com/SWE-bench/SWE-bench) tag v5.0.1 | 6,024 | MIT | 评测要 Docker。SWE-rebench 用的是 [SWE-rebench/SWE-bench-fork](https://github.com/SWE-rebench/SWE-bench-fork) 加预构建镜像，同样要 Docker |
| [SWE-agent/SWE-agent](https://github.com/SWE-agent/SWE-agent) v1.1.0（2025-05） | 20,558 | MIT | 自己再起环境。用 mini-swe-agent 的本地模式代替 |
| [microsoft/WindowsAgentArena](https://github.com/microsoft/WindowsAgentArena) v0.0.4 | 910 | MIT | Windows 客户机 |
| [google-research/android_world](https://github.com/google-research/android_world) | 951 | Apache-2.0 | 真机模拟器，要 AVD 和 KVM。启动参数 `-grpc 8554` |
| [THUDM/Android-Lab](https://github.com/THUDM/Android-Lab) | 328 | MIT | 无 release，同类模拟器缺口 |
| [laude-institute/terminal-bench](https://github.com/laude-institute/terminal-bench) | 2,600 | Apache-2.0 | 无 GitHub release。任务运行要 Docker，本次 **unverified** 是否有纯本地后端 |
| [ServiceNow/BrowserGym](https://github.com/ServiceNow/BrowserGym) v0.14.3 | 1,402 | SPDX NOASSERTION | 浏览器 gym。比 browser-use 更偏评测，网站任务经常要额外服务 |
| [web-arena-x/webarena](https://github.com/web-arena-x/webarena) v0.2.0（2023） | 1,627 | Apache-2.0 | 要自建一组网站 |
| [bytedance/deer-flow](https://github.com/bytedance/deer-flow) v2.1.0 | 83,873 | MIT | OpenSandbox 有示例，但是长程 harness，不是一条钉死的无头 CLI。本次没有核实单次调用参数，不放进 25 条实施清单 |
| AutoGPT | 187,580 | SPDX NOASSERTION | 平台，不是一块沙箱模板 |

## 6. 已经点名的需求：可行性（不重新论证取舍）

这些是既有需求。目录里已经有的不再建议新建。没有的只写极速版上能不能跑。

| 需求 | 可行性 | 说明 |
|---|---|---|
| Claude Code | 已有 `claude-code`。Express：yes | E2B 别名 `claude`。无头 `claude --dangerously-skip-permissions -p`。密钥 `ANTHROPIC_API_KEY`，本环境没有 |
| Codex | 已有 `codex` 与 `codex-agent-api`。Express：yes | E2B 别名 `codex`。`codex exec --full-auto` |
| OpenCode | 已有 `opencode`（experimental）。Express：yes | E2B 别名 `opencode`。`opencode run`。钉的是 `opencode-ai@1.19.0`，上游仓库 2026-10-15 仍在更新，升级版本是另一件事 |
| Amp | 已有 `amp`（experimental）。Express：yes | E2B 别名 `amp`。`amp --dangerously-allow-all -x`。密钥 `AMP_API_KEY` |
| Droid | 已有 `droid`（experimental）。Express：yes | E2B 别名 `droid`。本仓库命令是 `droid exec`，包 `@factory/cli@0.241.1`。E2B 文档写 `droid exec --auto low` |
| OpenClaw | 已有 `openclaw`。Express：yes | E2B 别名 `openclaw`。入口是 gateway，不是 ` -p ` |
| SWE（SWE-bench / SWE-agent） | 官方 harness：no | 每个实例一个 Docker 镜像。极速版不能起兄弟容器。可做的子集是 `mini-swe-agent` 本地模式，见 backlog |
| OSWorld | 完整评测：no | 要桌面虚拟机、截图和输入注入的客户机。可做的子集是 `linux-desktop`（Xvfb），不能跑 OSWorld 分数 |
| WAA | no | Windows 客户机。极速版是 Linux 容器 |
| 手机沙箱 | no | 没有设备或厂商协议。沙箱 API 没有手机这种资源 |
| Android World | no | 模拟器要 AVD 和 `/dev/kvm`。E2B `android-16` 是他们 microVM 里的 redroid，不能搬进无 KVM 的容器 |
| Grok | partial | 命令形状可行：`grok --always-approve -p`，密钥 `XAI_API_KEY`（本环境没有）。安装仍是未钉版本的 `https://x.ai/cli/install.sh`。没有公开的 CLI 仓库。E2B 已有别名 `grok`。钉住二进制之前不要建目录 |
| Pi（E2B `pi`） | yes | 见 `pi`。本目录不会变成 E2B 上的公开别名 `pi`。无头调用以 v1.2.0 的 `--help` 为准 |
| K3s | no | 要特权、cgroup、常常还要 `/dev/kmsg`。E2B `e2b/k3s` 能跑是因为 microVM。极速版没有这些 |
| Omarchy | no | 整机 Arch + Hyprland，没有可调用的无头 CLI |
| qm | no | 后端路由和租约不在 `agent_sandbox.server` 的命名命令里。把源码 COPY 进镜像得不到那些后端 |
| qm-sandbox | no | 文档中的具体接法是 Superserve 模板 `qm-agent-0.1.0`。极速版的安装命令不会注册那块模板 |

## 7. 建议升级，不是新目录

- `hermes-agent`：E2B 别名 `hermes` 装的是真 CLI。本仓库描述写明不注册工具。升级应钉 [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) v0.22.1（2026-10-14，MIT），命令 `hermes chat -Q --yolo -q "<prompt>"`，密钥按所选 provider（E2B 示例是 `OPENROUTER_API_KEY`）。安装方式要在 v0.22.1 的 README 里钉成包或二进制，本次没有打开那个 README，安装命令 **unverified**。
- `gemini`：保持 experimental，直到带密钥的 e2e 输出含 `ABX_E2E_OK`。
- `qoder`：官方描述没有安装 Qoder CLI。若上游给出可钉版本的无头命令，再补进这个目录，不要新建 `qoder-cli`。
- `browser-automation`：若 `playwright-mcp` 只是在现有 Chromium 上多一个进程，优先加命名命令，而不是第二个浏览器镜像。
- `opencode`：包仍是 1.19.0，上游仓库非常活跃。升级版本时保持 experimental，直到密钥 e2e 通过。

## 8. 建议新建的模板（P0 在前）

可行性：`yes` 表示按实施说明可以落在极速版上；`partial` 表示有一条能跑的子集，或安装/体积/无头参数还没核实死；`no` 没有放进这张表。完整字段在 `docs/template-backlog.json`。

| 排序 | name | 优先级 | 可行性 | 一句话 |
|---|---|---|---|---|
| 1 | kimi-code | P0 | yes | Moonshot 现行 CLI，npm `@moonshot-ai/kimi-code@2.2.0`，要在镜像里装 Node 22 |
| 2 | goose | P0 | yes | v1.54.0 的 linux gnu tarball，`goose run -t` |
| 3 | pi | P0 | yes | v1.2.0 的 `pi-linux-x64.tar.gz`，E2B/Vercel 都预装 |
| 4 | browser-use | P0 | yes | 0.13.11，无头 Chromium 上的浏览器 agent |
| 5 | code-interpreter | P0 | partial | 只做 Jupyter + pandas/numpy/matplotlib；全量 E2B 科学栈先不要 |
| 6 | linux-desktop | P0 | partial | Xvfb + noVNC，不是 OSWorld |
| 7 | cursor-agent | P1 | partial | `agent -p` 已有文档，安装脚本不钉版本 |
| 8 | grok | P1 | partial | 命令已知，安装不钉版本，先不要建目录 |
| 9 | code-server | P1 | yes | code-server 4.141.0 |
| 10 | mini-swe-agent | P1 | partial | 本地改仓库；不跑 SWE-bench Docker |
| 11 | aider | P1 | yes | `aider-chat==0.86.0`，上游 2025-08 后无 release |
| 12 | playwright-mcp | P1 | yes | `@playwright/mcp@0.0.83`，能并进 browser-automation 就不要新目录 |
| 13 | document-tools | P1 | yes | pandoc + `soffice --headless` |
| 14 | dev-services | P1 | yes | 用户态 Postgres 和 Redis，不用 Docker |
| 15 | copilot-cli | P1 | partial | 最新 release 是预发布，无头参数未在上游页核实 |
| 16 | crush | P1 | partial | 仓库活跃，可见 release 只有 nightly |
| 17 | cline | P1 | partial | v4.1.24 声称有 CLI，argv 未核实 |
| 18 | deepagents | P1 | partial | 包 0.7.25 已发布，是否有控制台脚本未核实 |
| 19 | tau2-bench | P1 | yes | 工具调用评测，不要虚拟机 |
| 20 | polyglot-toolchain | P1 | partial | 各钉一个 Go、Rust、Java，先量 rootfs |
| 21 | ocr | P2 | yes | tesseract |
| 22 | media-tools | P2 | yes | CPU 版 ffmpeg |
| 23 | stagehand | P2 | partial | 和 browser-use 重叠，Node API 未钉 |
| 24 | prime-agent | P2 | partial | E2B 有别名，可见 release 只有 nightly |
| 25 | appworld | P2 | partial | v0.1.3.post1，是否调用 Docker 未核实 |

不在表里、明确不要建的：`k3s`、`omarchy`、`qm`、`qm-sandbox`、`osworld`、`windows-agent-arena`、`android-world`、`phone-sandbox`、`swe-bench`（官方 harness）、`terminal-bench`、`skyvern`、`deer-flow`、`webarena`。

## 9. 实施说明（每条一段）

实施代理按 `docs/template-backlog.json` 的字段做。命名命令用 `@command`，提示词不要拼进 shell。密钥只来自环境变量，`template.yaml` 里值为空。`FROM` 平台基础镜像，运行时 `USER user`，不要 `CMD`/`ENTRYPOINT`。下面是同一份清单的可读版。

**kimi-code（P0，yes）。** [MoonshotAI/kimi-code](https://github.com/MoonshotAI/kimi-code) MIT，release `@moonshot-ai/kimi-code@2.2.0`（2026-10-14）。旧仓库 `MoonshotAI/kimi-cli` 已归档。npm 说明要求 Node ≥ 22.19，极速版基础镜像是 Node 20，所以 Dockerfile 里另装 Node 22 再 `npm install -g @moonshot-ai/kimi-code@2.2.0`。不要用 `code.kimi.com` 的安装脚本。无头命令写成 `kimi`，参数 `-p`；仓库 backlog 还写过 `kimi --print -p`。在 2.2.0 上跑 `kimi --help` 再冻结。密钥名以该版本的文档为准，本次 **unverified**。不需要 GPU、KVM、Docker 或显示器。OpenSandbox 示例仍 `pip install kimi-cli`，不要跟着装归档包。

**goose（P0，yes）。** [block/goose](https://github.com/block/goose) Apache-2.0，v1.54.0（2026-10-08）。下载 `goose-x86_64-unknown-linux-gnu.tar.bz2`（80,909,320 字节），不要 vulkan/cuda 包，也不要 `releases/download/stable/download_cli.sh`。命名命令 `goose`，调用 `goose run -t "<text>"`。模型密钥取决于配置的 provider。CLI 压缩包约 80MB，桌面端 Flatpak 不要装。

**pi（P0，yes）。** [badlogic/pi-mono](https://github.com/badlogic/pi-mono) MIT，v1.2.0（2026-10-12），npm 名 `@earendil-works/pi-coding-agent`。优先用 release 里的 `pi-linux-x64.tar.gz`（42,611,136 字节）。这个包是否自带 Node **unverified**；若没有，再按 [pi.dev quickstart](https://pi.dev/docs/latest/quickstart) 用 Node ≥ 22.19 和 `npm install -g --ignore-scripts @earendil-works/pi-coding-agent@1.2.0`。E2B 文档写 `pi -p`；[pi.dev CLI](https://pi.dev/docs/latest/cli) 写 `--print` 才是跑完即退出，`--mode text` 在终端上不会强制单次执行。以 v1.2.0 的 `--help` 为准。密钥 `ANTHROPIC_API_KEY` 或 Pi 支持的其它 provider。没有权限弹窗，进程用户能做什么它就能做什么，所以只能放在沙箱里。本目录不会注册 E2B 别名 `pi`。

**browser-use（P0，yes）。** [browser-use/browser-use](https://github.com/browser-use/browser-use) MIT，0.13.11（2026-10-07）。`pip install browser-use==0.13.11`，Chromium 用该版本依赖的 Playwright 构建，无头参数沿用 `browser-automation`（含 `/dev/shm` 不足时的 `--disable-dev-shm-usage`）。命名命令 `browser_use`，入参是任务文本。0.13.11 的 Agent 构造参数本次没有重读 README，编码前从该 tag 抄，不要凭记忆。需要模型密钥。不需要 GPU、KVM、Docker。E2B 的 `kernel-browser` 把 Browser Use 放在沙箱里、浏览器放在 Kernel；我们没有 Kernel，浏览器就在本沙箱。

**code-interpreter（P0，partial）。** 对齐 E2B `code-interpreter-v1` 和 OpenSandbox `code-interpreter:v1.1.0` 的能力，不要复制两边的 Dockerfile。第一版只钉 2026-10-15 从 `e2b-dev/code-interpreter` main 的 `template/requirements.txt` 里看到的 jupyter-server==2.20.0、ipykernel==6.31.0、pandas==2.2.3、numpy==2.3.5、matplotlib==3.10.9、pillow==12.3.0。命名命令 `execute_code`（language、code）和 `list_runtimes`。不要把 spacy、opencv、librosa、numba 放进第一版，它们对 10G rootfs 是否装得下 **unverified**。不要公开 Jupyter 端口，除非后面真的需要。CPU wheel only。Java/Go 多版本留给 `polyglot-toolchain`，不要在这里做切换脚本。

**linux-desktop（P0，partial）。** 对齐 E2B desktop 和 OpenSandbox `examples/desktop` 的能力：Xvfb、x11vnc 或等价 VNC、fluxbox 或一套更小的窗口管理器、noVNC、xdotool、scrot。不要复制它们的 Dockerfile。apt 版本写进构建日志。进程由命名命令 `desktop_start`、`screenshot`、`input` 拉起，不要写进 ENTRYPOINT。noVNC 端口 6080。密码来自环境变量。非 root 起 X、以及 XFCE 全量包的体积，本次 **unverified**，所以先用 fluxbox。这不是 OSWorld，不要装评测 harness。

**cursor-agent（P1，partial）。** [Cursor headless 文档](https://cursor.com/docs/cli/headless) 写安装命令 `curl https://cursor.com/install -fsS | bash`，调用 `agent -p "<prompt>"`，密钥 `CURSOR_API_KEY`，可选 `--output-format json` 和 `--force`。没有找到可钉版本的二进制 URL，所以现在不要合并目录。找到带校验和的版本后再建。二手 SWE 脚本里的 `--trust --sandbox disabled` 没有出现在这份 headless 页上，不要默认加上。不需要 GPU、KVM、Docker。

**grok（P1，partial）。** 只记录可行性，钉住安装物之前不要建目录。E2B [grok 页](https://docs.e2b.dev/agents/grok.md) 的调用是 `grok --always-approve -p "<prompt>"`，密钥 `XAI_API_KEY`。安装仍是未钉版本的 shell 脚本。`xai-org/grok` 是模型权重仓库，不是 CLI。不需要 GPU 或 KVM。本环境没有 xAI 密钥，L3 跑不通，L0 可以只断言二进制存在。

**code-server（P1，yes）。** [coder/code-server](https://github.com/coder/code-server) MIT，v4.141.0（2026-10-08）。解压 `code-server-4.141.0-linux-amd64.tar.gz`（239,926,515 字节）。命名命令 `code_server_start`，监听 8443，密码来自环境变量。没有模型调用。压缩包 240MB，加上平台镜像后是否仍低于约 10G **unverified**，构建时看 `df`。OpenSandbox 的 `opensandbox/vscode:latest` 未钉版本，不要 `FROM` 它。

**mini-swe-agent（P1，partial）。** [SWE-agent/mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent) MIT，v2.4.6（2026-07-23）。`pip install mini-swe-agent==2.4.6`，只用直接改本地文件系统的后端。命名命令 `mini_swe`。v2.4.6 的准确 argv 本次没有重读，从该 tag 的 README 抄。不要启用 Docker 或 bubblewrap。不要把 SWE-bench 打分放进这个模板。需要模型密钥和沙箱里的一份 git 仓库。

**aider（P1，yes）。** [Aider-AI/aider](https://github.com/Aider-AI/aider) Apache-2.0，v0.86.0（2025-08-09），仓库最后推送 2026-05-22。`pip install aider-chat==0.86.0`。命名命令 `aider`，调用 `aider --yes --message "<prompt>"`，工作目录必须是 git 仓库。密钥 `OPENAI_API_KEY` 或 `ANTHROPIC_API_KEY`，由 `--model` 决定。不需要 Docker。排在 P1 是因为一年多没有新 release，不是因为装不上。

**playwright-mcp（P1，yes）。** [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp) Apache-2.0，v0.0.83（2026-09-28）。`npm install -g @playwright/mcp@0.0.83`。命名命令 `mcp_start`，进程 `npx @playwright/mcp@0.0.83 --headless --port 8931`（端口以该版本 `--help` 为准，若 flag 不同就改）。若 `browser-automation` 的镜像已经能装下这个包，把命令加进那个目录，不要再建一个 Chromium 镜像。不需要模型密钥。

**document-tools（P1，yes）。** Debian 钉死版本的 `pandoc` 和 `libreoffice-writer`。命名命令 `convert`，按输出后缀选择 pandoc 或 `soffice --headless --convert-to`。给 soffice 单独的 `HOME`。非 root 是否还要额外字体包 **unverified**，缺字体时在 README 写明。不需要密钥、GPU 或显示器。许可证：pandoc GPL-2.0，LibreOffice MPL-2.0，在 README 里写清楚。

**dev-services（P1，yes）。** 钉死版本的 PostgreSQL 和 Redis，数据目录放在 `/home/user`，用 `pg_ctl` 和 `redis-server` 由用户拉起，不要用要 root 的 init 脚本。命名命令 `services_start`、`services_stop`，就绪检查 5432 和 6379。这是 Docker Compose 的替代，不是 Kubernetes。非 root 初始化本次没有在极速版上跑过，实施时若失败再改，不要退回到 DinD。

**copilot-cli（P1，partial）。** [github/copilot-cli](https://github.com/github/copilot-cli) 许可证 SPDX 为 NOASSERTION。2026-10-15 API 返回的最新 release 是预发布 `v1.0.99-0`。OpenSandbox 有 `github-copilot-cli-sandbox` 示例。无头参数没有在 GitHub 文档页上核实；二手页面写 `copilot -p` 和 `--allow-all-tools`。等一个非预发布的 npm 或 release 资产再做。密钥名 **unverified**。

**crush（P1，partial）。** [charmbracelet/crush](https://github.com/charmbracelet/crush)，SPDX NOASSERTION，28,642 stars，2026-10-15 仍在推送。API 返回的最新 release 是预发布 `nightly`。二手页面写 npm `@charmland/crush` 和 `crush --yolo`，两者都 **unverified**。有稳定 tag 或 npm 版本之后再做成 `crush` 命令。

**cline（P1，partial）。** [cline/cline](https://github.com/cline/cline) Apache-2.0，v4.1.24（2026-10-13），70,337 stars。仓库自述包含 CLI。npm 包名和无头 argv 本次 **unverified**（二手页面写 `cline --yolo`）。从 tag v4.1.24 读出 CLI 的安装行和「传入任务并退出」的参数后再建。不要装 VS Code 扩展。

**deepagents（P1，partial）。** [langchain-ai/deepagents](https://github.com/langchain-ai/deepagents) MIT，release `deepagents==0.7.25`（2026-10-14）。`pip install deepagents==0.7.25`。是否自带控制台脚本 **unverified**。若没有，命名命令 `deepagents` 用一段短 Python 跑一轮，工具落在本沙箱文件系统上，不要再去创建 E2B 或 OpenSandbox。需要模型密钥。OpenSandbox 和 E2B 都有集成文档，但 E2B 没有公开别名。

**tau2-bench（P1，yes）。** [sierra-research/tau2-bench](https://github.com/sierra-research/tau2-bench) MIT，v1.0.1（2026-07-22）。按该 tag 安装，PyPI 名若对不上就钉 git tag。命名命令 `tau2_run`，跑一个 domain。准确模块路径本次没有重读，从 v1.0.1 README 抄。任务是模拟的，不需要浏览器、Docker 或 KVM。需要模型密钥，用户模拟器往往还要第二份调用。这是评测模板，排在编码 CLI 后面。

**polyglot-toolchain（P1，partial）。** 各装一个钉死的官方包：Go 1.25.x、一个明确版本的 rustup toolchain、Temurin 21。不要做 OpenSandbox 那种多版本切换。命名命令 `toolchain_versions`。三者加在一起是否超过约 10G rootfs **unverified**，超了就只留 Go 和 Java。不需要密钥。Node 20 已经在基础镜像里，不要再装一份 Node，除非某个 CLI（Kimi、Pi）自己的目录要求 Node 22。

**ocr（P2，yes）。** 钉死 `tesseract-ocr` 和 `tesseract-ocr-eng`。命名命令 `ocr`，对一张图片跑 `tesseract <path> stdout`。不需要密钥或 GPU。

**media-tools（P2，yes）。** 钉死 Debian 的 `ffmpeg`，不要 CUDA，不要非自由编解码如果许可证说不清。命名命令 `transcode`，参数是列表不是 shell 字符串。构建日志里记下这个包实际启用的许可证。

**stagehand（P2，partial）。** [browserbase/stagehand](https://github.com/browserbase/stagehand) MIT。API 返回的最新 release 是 `stagehand-server-v3/v3.7.6`（2026-08-28）。npm 包版本本次没有核对。本地无头 Chromium 优先于 Browserbase。和 browser-use 重叠，只有调用方明确要 Node SDK 时再做。v3 API **unverified**。

**prime-agent（P2，partial）。** [PrimeIntellect-ai/prime-agent](https://github.com/PrimeIntellect-ai/prime-agent)，SPDX NOASSERTION。E2B 别名 `prime`，命令 `prime-agent -p`，密钥 `ANTHROPIC_API_KEY`，没有自动批准开关。2026-10-15 可见的最新 release 是预发布 `nightly`。没有稳定钉之前不要建目录。文档提到常驻 IPython，额外依赖 **unverified**。

**appworld（P2，partial）。** [stonybrooknlp/appworld](https://github.com/stonybrooknlp/appworld) Apache-2.0，v0.1.3.post1（2026-02-17）。是否在运行时调用 Docker **unverified**。若 README 要求 Docker，放弃。否则命名命令 `appworld_run` 跑一道题。优先做完 `tau2-bench`。

## 10. 实施顺序

1. P0 里可行性为 yes 的三条 CLI：`kimi-code`、`goose`、`pi`。每条都是一个二进制加一段提示词，和现有 `gemini` 相同。
2. `browser-use`，复用 `browser-automation` 的 Chromium 做法。
3. `code-interpreter` 的瘦身版，和 `linux-desktop` 的 fluxbox 版。这两条先做体积和非 root 试验，失败就停在 experimental，不要扩到 OSWorld 或全量科学栈。
4. P1 里安装已经钉死的：`code-server`、`aider`、`document-tools`、`dev-services`、`tau2-bench`、`mini-swe-agent`（仅本地后端）。
5. `cursor-agent`、`grok`、`crush`、`copilot-cli`、`cline`、`prime-agent` 在有可复现安装物之前保持在本文，不建目录。
6. 同时升级 `hermes-agent`，那不是新名字。
